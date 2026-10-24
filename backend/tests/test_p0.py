import io
import math
import pytest
from backend import demo, store
from backend.ai import validate_grounding
from backend.models import AIExplanation

def test_demo_numeric_accuracy_lineage_and_labels(client):
    response = client.post('/api/demo')
    assert response.status_code == 200, response.text
    state = client.get('/api/state').json()
    assert state['synthetic'] and len(state['inventory']) == 60
    assert state['scan']['rows_checked'] == 5522
    gold = demo.generate()[1]
    for kind, expected in gold.items():
        assert {i['subject'] for i in state['issues'] if i['kind'] == kind} == set(expected)
    issue = next(i for i in state['issues'] if i['kind'] == 'stockout')
    facts = issue['facts']
    assert math.isclose(facts['cover_days'], facts['on_hand']/(facts['total_sales']/facts['observation_days']), abs_tol=.0051)
    assert facts['observation_days'] == 90
    assert len(issue['evidence'][1]['values']['contributing_rows']) == 90
    ev = issue['evidence'][0]
    assert ev['cells']['on_hand'] == f"D{ev['row']}"
    original = client.get(f"/api/datasets/{ev['dataset_id']}/original")
    assert original.status_code == 200 and original.content.startswith(b'sku,item,')

def test_xlsx_mapping_and_immutable_original(client):
    content = demo.workbook_sample()
    response = client.post('/api/import', files={'file': ('stock.xlsx', content)})
    assert response.status_code == 200, response.text
    dataset = response.json()
    assert dataset['sheet'] == 'Inventory'
    result = client.post(f"/api/datasets/{dataset['id']}/mapping", json=dataset['suggestion'])
    assert result.status_code == 200
    assert result.json()['valid_rows'] == 60
    assert client.get(f"/api/datasets/{dataset['id']}/original").content == content
    assert client.post(f"/api/datasets/{dataset['id']}/mapping", json=dataset['suggestion']).status_code == 409

def test_quarantine_dates_negative_and_infinite(client):
    content = b'sku,date,qty,unit\nA,01/02/2026,2,each\nA,2026-10-01,-2,each\nB,2026-10-01,inf,each\nC,2026-10-01,4,each\n'
    dataset = client.post('/api/import',files={'file':('sales.csv',content)}).json()
    result = client.post(f"/api/datasets/{dataset['id']}/mapping",json=dataset['suggestion']).json()
    assert result['valid_rows'] == 1 and result['quality_count'] == 3
    quality = client.get('/api/state').json()['quality']
    assert quality[0]['cell'] == 'B2'
    assert client.post('/api/corrections',json={'dataset_id':dataset['id'],'row':2,'field':'date','proposed_value':'2026-02-01','reason':'Verified day-first source'}).status_code==200
    assert client.get('/api/export/corrections').content.count(b'2026-02-01')==1
    assert client.get(f"/api/datasets/{dataset['id']}/original").content==content

def test_unit_mismatch_suppresses_stockout(client):
    client.post('/api/demo')
    sales = next(d for d in store.all_records('datasets') if d['kind']=='sales')
    rows = store.get('validated', sales['id'])
    for row in rows['rows']:
        if row['sku']=='SKU-001': row['unit']='case'
    store.put('validated', rows)
    client.post('/api/scan',json={'as_of':'2026-10-24'})
    state=client.get('/api/state').json()
    assert not any(i['kind']=='stockout' and i['subject']=='SKU-001' for i in state['issues'])
    assert next(r for r in state['inventory'] if r['sku']=='SKU-001')['compatible_units'] is False

def test_no_approval_without_grounded_ai_and_stale_export(client):
    client.post('/api/demo')
    issue=next(i for i in store.all_records('issues') if i['kind']=='stockout' and i['subject']=='SKU-001')
    assert client.post(f"/api/issues/{issue['id']}/proposal",json={}).status_code==409
    assert client.get('/api/export/actions').status_code==409
    # Explicit test fixture only, never a production fallback.
    issue['ai']={'next_step':'Please check the open delivery before ordering.','model':'test-fixture','evidence_ids':[issue['evidence'][0]['id']]}
    store.put('issues',issue)
    action=client.post(f"/api/issues/{issue['id']}/proposal",json={}).json()
    assert client.get('/api/export/actions').status_code==409
    response=client.post(f"/api/actions/{action['id']}/decision",json={'decision':'approved','body':action['body']})
    assert response.status_code==200
    assert client.get('/api/export/actions').status_code==200
    assert client.post(f"/api/actions/{action['id']}/decision",json={'decision':'rejected'}).status_code==409
    inv=next(d for d in store.all_records('datasets') if d['kind']=='inventory')
    rows=store.get('validated',inv['id']); rows['rows'][0]['on_hand']=9999; store.put('validated',rows)
    client.post('/api/scan',json={'as_of':'2026-10-24'})
    assert store.get('actions',action['id'])['status']=='stale'
    assert client.get('/api/export/actions').status_code==409

def test_model_unknown_evidence_or_number_withheld(client):
    client.post('/api/demo'); issue=store.all_records('issues')[0]
    with pytest.raises(ValueError,match='unknown source'):
        validate_grounding(AIExplanation(explanation='Check the stock before ordering.',next_step='Please review the original record.',evidence_ids=['invented']),issue)
    with pytest.raises(ValueError,match='introduced a number'):
        validate_grounding(AIExplanation(explanation='Purchase 987654 units immediately.',next_step='Please review the original record.',evidence_ids=[issue['evidence'][0]['id']]),issue)

def test_snapshots_are_not_silently_combined(client):
    client.post('/api/demo')
    dataset=client.post('/api/import',files={'file':('inventory.csv',demo.generate()[0]['inventory.csv'])}).json()
    assert client.post(f"/api/datasets/{dataset['id']}/mapping",json=dataset['suggestion']).status_code==409
    assert client.post('/api/demo').status_code==409

def test_future_sales_excluded_and_sparse_flagged(client):
    client.post('/api/demo')
    response=client.post('/api/scan',json={'as_of':'2026-07-28'})
    assert response.status_code==200
    state=client.get('/api/state').json()
    assert all(row['sparse'] for row in state['inventory'])
    assert next(i for i in state['issues'] if i['kind']=='stockout')['facts']['observation_days']==2

def test_oversize_and_subcent_numbers_quarantined(client):
    content=b'invoice_id,supplier,date,amount,currency\nA,Test,2026-10-01,130.001,USD\nB,Test,2026-10-01,1e308,USD\nC,Test,2026-10-01,130.01,USD\n'
    dataset=client.post('/api/import',files={'file':('invoices.csv',content)}).json()
    result=client.post(f"/api/datasets/{dataset['id']}/mapping",json=dataset['suggestion']).json()
    assert result['valid_rows']==1 and result['quality_count']==2
