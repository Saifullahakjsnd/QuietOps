"""As-of features and purged chronological evaluation for lead-window demand risk."""
import hashlib
import json
import math
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
import numpy as np
import pandas as pd
from .engine import evidence, stable_id
from . import tabpfn_adapter

FEATURES = ['on_hand', 'lead_days', 'daily_90', 'daily_28', 'daily_7',
            'recent_ratio', 'volatility_28', 'cover_90', 'cover_7']
TARGET = 'Sales in the next supplier lead-time window exceed on-hand stock, assuming no incoming receipt.'
LIMITS = ['Synthetic examples demonstrate mechanics, not real-shop accuracy or calibrated probabilities.',
          'Observed sales are not latent demand: past stockouts can censor sales.',
          'No dated receipt or supplier-performance history exists; incoming orders are excluded.',
          'Inventory and lead time must be known at each historical date; current snapshots are never backfilled.',
          'Same products recur across time; this evaluates later dates, not unseen shops or suppliers.',
          'Threshold fixed at 0.50 before evaluation. No confidence interval is claimed for individual probabilities.']

def input_fingerprint(tables, as_of):
    return hashlib.sha256(json.dumps({'as_of': str(as_of), 'tables': tables, 'features': FEATURES,
                                     'schema': 1}, sort_keys=True).encode()).hexdigest()

def index_sales(tables):
    result = defaultdict(list)
    for row in tables.get('sales', []):
        result[row['sku']].append(row)
    return result

def features(snapshot, sales, as_of):
    rows = [r for r in sales if as_of-timedelta(days=89) <= date.fromisoformat(r['date']) <= as_of]
    if not rows or any(r['unit'] != snapshot['unit'] for r in rows):
        raise ValueError('Missing or incompatible sales units.')
    daily = defaultdict(float)
    for row in rows:
        daily[row['date']] += row['qty']
    if len(daily) < 28:
        raise ValueError('Fewer than 28 distinct observed sales dates.')
    days = (as_of-date.fromisoformat(min(daily))).days+1
    qty90 = sum(daily.values()) / days  # Same denominator as the existing stock-cover rule.
    recent = [daily.get((as_of-timedelta(days=k)).isoformat(), 0) for k in range(28)]
    qty28, qty7 = sum(recent)/28, sum(recent[:7])/7
    if qty90 <= 0:
        raise ValueError('No positive demand history.')
    values = dict(zip(FEATURES, [snapshot['on_hand'], snapshot['lead_days'], qty90, qty28, qty7,
                                qty7/max(qty28, .001), float(np.std(recent)),
                                snapshot['on_hand']/qty90, snapshot['on_hand']/max(qty7, .001)]))
    sources = [evidence(snapshot, description='As-of inventory and supplier lead time')]
    groups = defaultdict(list)
    for row in rows:
        groups[row['_source']['dataset_id']].append(row)
    for group in groups.values():
        ev = evidence(group[0], description='Trailing sales only; exact contributing rows listed')
        ev['values'] = {'sku': snapshot['sku'], 'contributing_rows': [r['_source']['row'] for r in group],
                        'first_date': min(r['date'] for r in group), 'last_date': max(r['date'] for r in group),
                        'quantity_sum': sum(r['qty'] for r in group), 'unit': snapshot['unit']}
        sources.append(ev)
    return values, sources

def historical_examples(tables, as_of):
    indexed = index_sales(tables)
    examples, skipped, seen = [], [], set()
    for row in tables.get('stock_history', []):
        when = date.fromisoformat(row['date'])
        end = when+timedelta(days=math.ceil(row['lead_days']))
        key = (row['sku'], row['date'])
        if key in seen:
            raise ValueError('Duplicate SKU/date history across files; remove overlapping snapshots.')
        seen.add(key)
        if end > as_of:
            skipped.append({'sku': row['sku'], 'date': row['date'], 'reason': 'Outcome not mature as of scan.'})
            continue
        try:
            values, sources = features(row, indexed[row['sku']], when)
            future = [s for s in indexed[row['sku']] if when < date.fromisoformat(s['date']) <= end]
            if any(s['unit'] != row['unit'] for s in future) or len({s['date'] for s in future}) != (end-when).days:
                raise ValueError('Outcome requires compatible sales observations on every horizon date (including explicit zero rows).')
            total = sum(s['qty'] for s in future)
            examples.append({'sku': row['sku'], 'as_of': when.isoformat(), 'label_end': end.isoformat(),
                             'features': values, 'label': int(total > row['on_hand']),
                             'future_sales': total, 'evidence': sources,
                             'outcome_rows': [evidence(s) for s in future]})
        except ValueError as error:
            skipped.append({'sku': row['sku'], 'date': row['date'], 'reason': str(error)})
    return sorted(examples, key=lambda e: (e['as_of'], e['sku'])), skipped

def chronological_split(examples):
    dates = sorted({e['as_of'] for e in examples})
    if len(dates) < 4:
        raise ValueError('Need at least four historical snapshot dates with mature, complete outcomes.')
    cutoff = dates[int(len(dates)*.65)]
    train = [e for e in examples if e['label_end'] < cutoff]
    test = [e for e in examples if e['as_of'] >= cutoff]
    if len(train) < 40 or len(test) < 20 or len({e['label'] for e in train}) < 2 or len({e['label'] for e in test}) < 2:
        raise ValueError('Need at least 40 training and 20 held-out examples, with both outcomes in each split.')
    return train, test, cutoff

def metrics(labels, predictions, probabilities=None):
    tp = sum(y == 1 and p == 1 for y, p in zip(labels, predictions))
    fp = sum(y == 0 and p == 1 for y, p in zip(labels, predictions))
    fn = sum(y == 1 and p == 0 for y, p in zip(labels, predictions))
    tn = sum(y == 0 and p == 0 for y, p in zip(labels, predictions))
    result = {'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn, 'support': len(labels),
              'precision': tp/(tp+fp) if tp+fp else 0, 'recall': tp/(tp+fn) if tp+fn else 0,
              'f1': 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0, 'accuracy': (tp+tn)/len(labels)}
    if probabilities is not None:
        from sklearn.metrics import average_precision_score, roc_auc_score
        result.update({'brier_score': sum((p-y)**2 for y, p in zip(labels, probabilities))/len(labels),
                       'roc_auc': float(roc_auc_score(labels, probabilities)),
                       'average_precision': float(average_precision_score(labels, probabilities))})
    return result

def run(tables, as_of, synthetic=False):
    examples, skipped = historical_examples(tables, as_of)
    train, test, cutoff = chronological_split(examples)
    indexed, live, excluded = index_sales(tables), [], []
    for snapshot in tables.get('inventory', []):
        try:
            values, sources = features(snapshot, indexed[snapshot['sku']], as_of)
            live.append((snapshot, values, sources))
        except ValueError as error:
            excluded.append({'sku': snapshot['sku'], 'reason': str(error)})
    if not live:
        raise ValueError('No current SKU has sufficient compatible sales history.')
    frame = lambda rows: pd.DataFrame(rows, columns=FEATURES)
    probabilities, model = tabpfn_adapter.predict(frame([e['features'] for e in train]), [e['label'] for e in train],
                                                 frame([e['features'] for e in test]+[v for _, v, _ in live]))
    heldout, current = probabilities[:len(test)], probabilities[len(test):]
    labels = [e['label'] for e in test]
    comparison = {
        'tabpfn': metrics(labels, [int(p >= .5) for p in heldout], heldout),
        'stock_cover_rule': metrics(labels, [int(e['features']['cover_90'] < e['features']['lead_days']) for e in test]),
        'recent_demand': metrics(labels, [int(e['features']['daily_7']*e['features']['lead_days'] > e['features']['on_hand']) for e in test])}
    fingerprint = input_fingerprint(tables, as_of)
    predictions = []
    for (row, values, sources), probability in zip(live, current):
        rule = values['cover_90'] < values['lead_days']
        recent = values['daily_7']*values['lead_days'] > values['on_hand']
        risk = probability >= .5
        facts = {**{k: round(v, 5) for k, v in values.items()}, 'probability': probability,
                 'probability_percent': round(probability*100, 1), 'rule_risk': rule, 'recent_demand_risk': recent,
                 'as_of': as_of.isoformat(), 'threshold': .5, 'training_rows': len(train), 'test_rows': len(test)}
        prediction = {'id': stable_id('predictive_stockout', row['sku']), 'kind': 'predictive_stockout',
                      'title': f"{row['item']}: look ahead", 'subject': row['sku'], 'supplier': row['supplier'],
                      'severity': 'high' if risk else 'low', 'status': 'open', 'ai': None,
                      'summary': f"{probability:.1%} model estimate of demand exceeding stock within {values['lead_days']} days, assuming no receipt.",
                      'calculation': f"TabPFN-3.5 estimate {probability:.1%}; review threshold 50%; trailing stock cover {values['cover_90']:.2f} days vs lead time {values['lead_days']} days. Recent daily sales {values['daily_7']:.2f} vs trailing {values['daily_90']:.2f}.",
                      'assumptions': LIMITS + ['Inventory is treated as current at the scan date. Confirm snapshot freshness.',
                                             'Features describe associations, not causal explanations; model estimates are uncalibrated.'],
                      'facts': facts, 'evidence': sources, 'predictive_risk': risk,
                      'overlooked_by_rule': risk and not rule, 'model': model,
                      'input_fingerprint': fingerprint}
        prediction['fingerprint'] = hashlib.sha256(json.dumps({k: prediction[k] for k in (
            'facts', 'evidence', 'assumptions', 'input_fingerprint')}, sort_keys=True).encode()+
            json.dumps({k: model.get(k) for k in ('checkpoint_sha256', 'package_version', 'n_estimators', 'seed')}, sort_keys=True).encode()).hexdigest()
        predictions.append(prediction)
    predictions.sort(key=lambda p: (-int(p['overlooked_by_rule']), -p['facts']['probability']))
    report = {'id': 'prediction-run', 'state': 'completed', 'at': datetime.now(timezone.utc).isoformat(),
              'as_of': as_of.isoformat(), 'input_fingerprint': fingerprint, 'target': TARGET,
              'synthetic': synthetic, 'limitations': LIMITS, 'model': model, 'comparison': comparison,
              'split': {'cutoff': cutoff, 'train_rows': len(train), 'test_rows': len(test),
                        'purged_rows': len(examples)-len(train)-len(test),
                        'latest_training_outcome': max(e['label_end'] for e in train),
                        'first_test_date': min(e['as_of'] for e in test),
                        'latest_test_outcome': max(e['label_end'] for e in test)},
              'skipped_history': skipped, 'excluded_skus': excluded, 'feature_names': FEATURES,
              'heldout': [{'sku': e['sku'], 'as_of': e['as_of'], 'label_end': e['label_end'],
                           'label': e['label'], 'features': e['features'], 'probability': p} for e, p in zip(test, heldout)],
              'training_digest': hashlib.sha256(json.dumps([{k: e[k] for k in ('sku', 'as_of', 'label_end', 'features', 'label')} for e in train], sort_keys=True).encode()).hexdigest()}
    return predictions, report
