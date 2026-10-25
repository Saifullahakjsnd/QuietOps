"""Unit fixtures below use an explicit fake adapter; the saved evaluation uses real weights."""
from datetime import date, timedelta
import copy
import pytest
from backend import ai, demo, predictive, predictive_demo, store, tabpfn_adapter
from backend.main import collect

def companion(client):
    assert client.post('/api/demo').status_code == 200
    assert client.post('/api/predictions/demo').status_code == 200

def fake_inference(train, labels, test):
    # Explicitly a test double for workflow tests, never an application fallback.
    probabilities = [.9 for _ in range(len(test))]
    return probabilities, {'model': 'test-double', 'inference_ran': False, 'latency_ms': 0,
                           'checkpoint_sha256': 'test-only', 'package_version': 'test', 'n_estimators': 0, 'seed': 42}

def test_features_never_read_future_sales_or_current_inventory(client):
    companion(client)
    tables = collect()
    original, _ = predictive.historical_examples(tables, demo.AS_OF)
    snapshot = tables['stock_history'][0]
    cutoff = date.fromisoformat(snapshot['date'])
    indexed = predictive.index_sales(tables)
    before, sources = predictive.features(snapshot, indexed[snapshot['sku']], cutoff)
    changed = copy.deepcopy(indexed[snapshot['sku']])
    for row in changed:
        if date.fromisoformat(row['date']) > cutoff:
            row['qty'] = 1e9
    after, _ = predictive.features(snapshot, changed, cutoff)
    assert before == after
    assert all(e['values'].get('last_date', str(cutoff)) <= str(cutoff) for e in sources)
    tables['inventory'][0]['on_hand'] = 1e9
    unchanged, _ = predictive.historical_examples(tables, demo.AS_OF)
    assert [e['features'] for e in original] == [e['features'] for e in unchanged]

def test_chronological_split_purges_unmatured_labels():
    examples = [{'sku': str(i), 'as_of': f'2026-01-{i:02}', 'label_end': f'2026-01-{i+2:02}', 'label': i%2}
                for i in range(1, 21) for _ in range(10)]
    train, test, cutoff = predictive.chronological_split(examples)
    assert max(e['label_end'] for e in train) < min(e['as_of'] for e in test)
    assert len(train)+len(test) < len(examples)

def test_original_demo_has_no_manufactured_historical_predictions(client):
    client.post('/api/demo')
    response = client.post('/api/predictions/run')
    assert response.status_code == 503
    assert 'historical' in response.json()['detail']
    assert client.get('/api/state').json()['predictions'] == []

def test_disabled_or_unaccepted_adapter_never_imports_or_runs_model(monkeypatch, tmp_path):
    monkeypatch.setattr(store, 'DATA', tmp_path)
    monkeypatch.delenv('QUIETOPS_TABPFN_LICENSE_ACCEPTED', raising=False)
    assert tabpfn_adapter.status()['state'] == 'license_required'
    with pytest.raises(RuntimeError, match='license'):
        tabpfn_adapter.predict(None, None, None)
    monkeypatch.setenv('QUIETOPS_TABPFN_ENABLED', '0')
    assert tabpfn_adapter.status()['state'] == 'disabled'
    with pytest.raises(RuntimeError, match='disabled'):
        tabpfn_adapter.predict(None, None, None)

def test_metrics_are_measured_not_perfect_by_construction():
    m = predictive.metrics([1, 1, 0, 0], [1, 0, 1, 0])
    assert (m['tp'], m['fp'], m['fn'], m['tn']) == (1, 1, 1, 1)
    assert m['precision'] == m['recall'] == m['f1'] == .5

def test_predictions_separate_lineage_approval_and_staleness(client, monkeypatch):
    companion(client)
    assert client.post('/api/predictions/demo').status_code == 409
    previous = client.get('/api/state').json()['issues']
    monkeypatch.setattr(tabpfn_adapter, 'predict', fake_inference)
    response = client.post('/api/predictions/run')
    assert response.status_code == 200, response.text
    state = client.get('/api/state').json()
    assert state['issues'] == previous
    risk = next(p for p in state['predictions'] if p['subject'] == 'SKU-007')
    assert risk['overlooked_by_rule'] and not risk['facts']['rule_risk']
    assert not risk['facts']['recent_demand_risk']
    assert len(risk['evidence']) == 3
    assert all(client.get(f"/api/datasets/{e['dataset_id']}/original").status_code == 200 for e in risk['evidence'])
    key = risk['id']
    assert client.post(f'/api/predictions/{key}/proposal').status_code == 409
    async def grounded(issue):
        return {'next_step': 'Please review delivery plans before considering a purchase.', 'explanation': 'Test explanation.',
                'model': 'test-double', 'evidence_ids': [issue['evidence'][0]['id']]}
    monkeypatch.setattr(ai, 'explain', grounded)
    assert client.post(f'/api/predictions/{key}/explain').status_code == 200
    action = client.post(f'/api/predictions/{key}/proposal').json()
    assert action['scope'] == 'prediction'
    assert client.get('/api/export/actions').status_code == 409
    assert client.post(f"/api/actions/{action['id']}/decision", json={'decision': 'approved', 'body': 'Edited supplier review; please check the demand surge and delivery plan.'}).status_code == 200
    assert b'Edited supplier review' in client.get('/api/export/actions').content
    client.post('/api/scan', json={'as_of': '2026-10-25'})
    assert store.get('actions', action['id'])['status'] == 'stale'
    assert client.get('/api/export/actions').status_code == 409
    assert client.post(f'/api/predictions/{key}/explain').status_code == 409
    client.post('/api/scan', json={'as_of': '2026-10-24'})
    assert client.post('/api/predictions/run').status_code == 200
    renewed = client.post(f'/api/predictions/{key}/proposal').json()
    assert renewed['id'] != action['id'] and renewed['status'] == 'draft'
    dataset = client.post('/api/import', files={'file': ('invalid.csv', b'sku,date,qty,unit\nX,2026-10-24,-1,each\n')}).json()
    assert client.post(f"/api/datasets/{dataset['id']}/mapping", json=dataset['suggestion']).status_code == 200
    assert store.get('actions', renewed['id'])['status'] == 'stale'
    assert client.post(f"/api/actions/{renewed['id']}/decision", json={'decision':'approved'}).status_code == 409

def test_history_future_outcomes_and_duplicates_are_withheld(client):
    companion(client)
    tables = collect()
    rows, skipped = predictive.historical_examples(tables, date(2026, 6, 1))
    assert rows and all(e['label_end'] <= '2026-06-01' for e in rows)
    assert skipped
    tables['stock_history'].append(tables['stock_history'][0])
    with pytest.raises(ValueError, match='Duplicate'):
        predictive.historical_examples(tables, demo.AS_OF)

def test_actual_inference_error_creates_no_substitute_probabilities(client, monkeypatch):
    companion(client)
    def failed(*args):
        raise RuntimeError('test checkpoint access denied')
    monkeypatch.setattr(tabpfn_adapter, 'predict', failed)
    response = client.post('/api/predictions/run')
    assert response.status_code == 503
    assert client.get('/api/state').json()['predictions'] == []
    assert any(e['action'] == 'Prediction withheld' for e in store.all_records('audit'))

def test_prediction_percentage_cannot_reuse_another_evidence_number():
    from backend.models import AIExplanation
    issue = {'kind': 'predictive_stockout', 'evidence': [{'id': 'source'}],
             'facts': {'probability_percent': 84.2, 'lead_days': 5}}
    result = AIExplanation(explanation='The model estimates 5% risk assuming no receipt.',
                           next_step='Please review the supplier delivery plan.', evidence_ids=['source'])
    with pytest.raises(ValueError, match='altered'):
        ai.validate_grounding(result, issue)
