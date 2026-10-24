"""Deterministic issue detection. The LLM cannot change calculations or evidence."""
import hashlib
import json
from datetime import date, timedelta
from difflib import SequenceMatcher
import duckdb
import pandas as pd

def stable_id(kind, key):
    return hashlib.sha256(f'{kind}:{key}'.encode()).hexdigest()[:16]

def evidence(row, fields=None, description=''):
    src = row['_source']
    fields = fields or [key for key in row if not key.startswith('_')]
    return {**src, 'id': f"{src['dataset_id'][:8]}-r{src['row']}",
            'cells': {key: value for key, value in src['cells'].items() if key in fields},
            'values': {field: row[field] for field in fields if field in row}, 'description': description}

def detect(tables, as_of: date):
    inventory = tables.get('inventory', [])
    sales = [row for row in tables.get('sales', []) if as_of-timedelta(days=89) <= date.fromisoformat(row['date']) <= as_of]
    orders = tables.get('orders', [])
    invoices = [row for row in tables.get('invoices', []) if date.fromisoformat(row['date']) <= as_of]
    issues, stock = [], []
    rates = {}
    if sales:
        frame = pd.DataFrame([{k: v for k, v in row.items() if k != '_source'} for row in sales])
        with duckdb.connect(':memory:') as db:
            db.register('sales_input', frame)
            rates = {r[0]: {'qty': float(r[1]), 'days': int(r[2]), 'first': str(r[3]), 'units': int(r[4]), 'unit': str(r[5])}
                     for r in db.execute('SELECT sku, SUM(qty), COUNT(DISTINCT date), MIN(date), COUNT(DISTINCT unit), MIN(unit) FROM sales_input GROUP BY sku').fetchall()}
    seen_skus = set()
    for row in inventory:
        sku = row['sku']
        if sku in seen_skus:
            continue
        seen_skus.add(sku)
        demand = rates.get(sku)
        matched_sales = [r for r in sales if r['sku'] == sku]
        days = (as_of-date.fromisoformat(demand['first'])).days+1 if demand else 0
        compatible = bool(demand and demand['units'] == 1 and demand['unit'] == row['unit'])
        daily = demand['qty']/days if compatible and days else 0
        cover = row['on_hand']/daily if daily > 0 else None
        sparse = not demand or demand['days'] < 14
        inv = {k: v for k, v in row.items() if k != '_source'}
        inv.update({'daily_sales': round(daily, 3), 'cover_days': round(cover, 1) if cover is not None else None,
                    'risk': cover is not None and cover < row['lead_days'], 'sparse': sparse, 'compatible_units': compatible})
        stock.append(inv)
        if cover is not None and cover < row['lead_days']:
            facts = {'on_hand': row['on_hand'], 'total_sales': demand['qty'], 'observation_days': days,
                     'daily_sales': round(daily, 3), 'cover_days': round(cover, 2), 'lead_days': row['lead_days']}
            sources = [evidence(row, description='Inventory snapshot and supplier lead time')]
            # Include every contributing row, grouped by file, with exact row ranges and an original-download link.
            groups = {}
            for sale in matched_sales:
                groups.setdefault(sale['_source']['dataset_id'], []).append(sale)
            for group in groups.values():
                rows = [s['_source']['row'] for s in group]
                ev = evidence(group[0], ['sku', 'date', 'qty', 'unit'], 'Sales aggregate; every listed row contributes')
                ev['values'] = {'sku': sku, 'contributing_rows': rows, 'quantity_sum': sum(s['qty'] for s in group),
                                'first_date': min(s['date'] for s in group), 'last_date': max(s['date'] for s in group), 'unit': row['unit']}
                sources.append(ev)
            issues.append({'id': stable_id('stockout', sku), 'kind': 'stockout', 'title': f"{row['item']} needs a stock check",
                           'subject': sku, 'supplier': row['supplier'], 'severity': 'high' if cover < 3 else 'medium',
                           'summary': f"{cover:.1f} days of stock against a {row['lead_days']:g}-day supplier lead time.",
                           'calculation': f"{row['on_hand']:g} on hand ÷ ({demand['qty']:g} sold ÷ {days} calendar days) = {cover:.2f} days cover < {row['lead_days']:g} days lead time",
                           'assumptions': ['Trailing observed demand continues; missing sales dates count as zero.', 'Incoming orders are not included; check open orders before reordering.', 'Inventory is treated as current at the scan date; confirm snapshot freshness.'] + (['Sparse data: fewer than 14 distinct sales dates; estimate is weak.'] if sparse else []),
                           'facts': facts, 'evidence': sources, 'status': 'open', 'ai': None})
    for row in orders:
        expected = date.fromisoformat(row['expected_date'])
        if expected < as_of and row['received_qty'] < row['ordered_qty']:
            days_late = (as_of-expected).days
            remaining = row['ordered_qty']-row['received_qty']
            issues.append({'id': stable_id('late_order', row['order_id']+':'+row['sku']), 'kind': 'late_order',
                           'title': f"{row['order_id']} is waiting on a delivery", 'subject': row['order_id'], 'supplier': row['supplier'],
                           'severity': 'high' if days_late >= 5 else 'medium', 'summary': f"{days_late} days overdue · {remaining:g} {row['unit']} still outstanding.",
                           'calculation': f"{as_of.isoformat()} − {expected.isoformat()} = {days_late} days late; {row['ordered_qty']:g} ordered − {row['received_qty']:g} received = {remaining:g} outstanding",
                           'assumptions': ['Expected date is the agreed delivery date.', 'Received quantity is cumulative as of the scan date.'],
                           'facts': {'days_late': days_late, 'ordered_qty': row['ordered_qty'], 'received_qty': row['received_qty'], 'remaining_qty': remaining},
                           'evidence': [evidence(row)], 'status': 'open', 'ai': None})
    # Exact candidate groups are distinct from fuzzy candidates. Never label fraud.
    groups = {}
    for row in invoices:
        key = (row['supplier'].strip().casefold(), row['invoice_id'].strip().casefold())
        groups.setdefault(key, []).append(row)
    for key, rows in groups.items():
        if len(rows) > 1:
            first = rows[0]
            issues.append({'id': stable_id('duplicate_exact', json.dumps(key)), 'kind': 'duplicate_exact',
                           'title': f"{first['invoice_id']} appears more than once", 'subject': first['invoice_id'], 'supplier': first['supplier'],
                           'severity': 'medium', 'summary': f"{len(rows)} rows share an invoice identifier and supplier. Verify before payment.",
                           'calculation': f"Normalized supplier + invoice ID match on {len(rows)} source rows; amounts: " + ', '.join(f"{r['currency']} {r['amount']:.2f}" for r in rows),
                           'assumptions': ['A duplicate identifier is a review candidate, not proof of a duplicate payment or fraud.', 'Credits and negative invoices are quarantined separately.'],
                           'facts': {'matching_rows': len(rows), 'amounts': [r['amount'] for r in rows]}, 'evidence': [evidence(r) for r in rows], 'status': 'open', 'ai': None})
    representatives = [rows[0] for rows in groups.values()]
    # Bucket by supplier, currency and exact cents before pair comparisons; cap large buckets.
    buckets = {}
    for row in representatives:
        buckets.setdefault((row['supplier'].casefold(), row['currency'], round(row['amount']*100)), []).append(row)
    for bucket in buckets.values():
        if len(bucket) > 200:
            raise ValueError('More than 200 same-supplier invoices share one amount; split the invoice batch for fuzzy comparison.')
        for i, left in enumerate(bucket):
            for right in bucket[i+1:]:
                if abs((date.fromisoformat(left['date'])-date.fromisoformat(right['date'])).days) > 3:
                    continue
                score = SequenceMatcher(None, left['invoice_id'].casefold(), right['invoice_id'].casefold()).ratio()
                if score < .7:
                    continue
                pair = sorted([left['invoice_id'], right['invoice_id']])
                issues.append({'id': stable_id('duplicate_fuzzy', left['supplier']+json.dumps(pair)), 'kind': 'duplicate_fuzzy',
                               'title': f"Check a possible copy of {left['invoice_id']}", 'subject': left['invoice_id'], 'supplier': left['supplier'],
                               'severity': 'low', 'summary': 'Same supplier, currency and amount; similar invoice IDs within three days.',
                               'calculation': f"Identifier similarity {score:.2f} ≥ 0.70; equal amount {left['currency']} {left['amount']:.2f}; date distance ≤ 3 days",
                               'assumptions': ['Fuzzy candidates can be legitimate separate transactions. Compare original invoices.', 'Exact currency/amount match, date distance ≤ 3 days, and ID similarity ≥ 0.70 are required.'],
                               'facts': {'similarity': round(score, 3), 'amount': left['amount']}, 'evidence': [evidence(left), evidence(right)], 'status': 'open', 'ai': None})
    issues.sort(key=lambda x: ({'high': 0, 'medium': 1, 'low': 2}[x['severity']], x['kind'], x['subject']))
    return issues, stock
