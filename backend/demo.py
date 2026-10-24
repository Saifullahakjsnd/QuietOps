"""Explicitly fictional reproducible dataset. Gold labels never enter detector input."""
import io
import random
from datetime import date, timedelta
import pandas as pd

AS_OF = date(2026, 10, 24)
SUPPLIERS = ['Northfield Foods', 'Oak & Grain', 'Daily Dairy Co.', 'Greenhouse Produce', 'Harbor Pantry', 'Sunrise Bakery', 'Meadow Mills', 'Kindred Coffee', 'Orchard Supply', 'Well & Good', 'Maple Trading', 'Cornerstone Goods']
PRODUCTS = ['Oat milk', 'Sourdough loaf', 'Free-range eggs', 'Cherry tomatoes', 'Jasmine rice', 'Greek yogurt', 'Rolled oats', 'House blend coffee', 'Apple juice', 'Olive oil', 'Wildflower honey', 'Dark chocolate', 'Almond butter', 'Sea salt crackers', 'Red lentils', 'Sparkling water', 'Coconut milk', 'Penne pasta', 'Tomato passata', 'Granola']

def generate():
    rng = random.Random(42)
    inventory, sales, orders, invoices = [], [], [], []
    for i in range(60):
        sku = f'SKU-{i+1:03}'
        rate = 2 + i % 7
        supplier = SUPPLIERS[i % 12]
        lead = 5 + i % 6
        inventory.append({'sku': sku, 'item': PRODUCTS[i % 20] + (f' · {i//20+1}' if i >= 20 else ''), 'supplier': supplier,
                          'on_hand': rate * (2 if i < 6 else 28), 'lead_days': lead, 'unit': 'each',
                          'unit_cost': round(1.5 + i * .31, 2), 'currency': 'USD'})
        for day in range(90):
            sales.append({'sku': sku, 'date': (AS_OF - timedelta(days=89-day)).isoformat(), 'qty': rate + rng.choice([-1, 0, 0, 1]), 'unit': 'each'})
        if i < 24:
            orders.append({'order_id': f'PO-{2020+i}', 'sku': sku, 'supplier': supplier,
                           'expected_date': (AS_OF + timedelta(days=-3-i if i < 4 else 4+i)).isoformat(),
                           'ordered_qty': 60, 'received_qty': 20 if i < 4 else 0, 'unit': 'each'})
    for i in range(36):
        invoices.append({'invoice_id': f'INV-{4100+i}', 'supplier': SUPPLIERS[i % 12],
                         'date': (AS_OF-timedelta(days=2+i)).isoformat(), 'amount': round(130+i*23.65, 2), 'currency': 'USD'})
    invoices.append(dict(invoices[0]))
    fuzzy = dict(invoices[1]); fuzzy['invoice_id'] += '-COPY'; invoices.append(fuzzy)
    files = {f'{kind}.csv': pd.DataFrame(rows).to_csv(index=False).encode() for kind, rows in [('inventory', inventory), ('sales', sales), ('orders', orders), ('invoices', invoices)]}
    gold = {'stockout': [f'SKU-{i+1:03}' for i in range(6)], 'late_order': [f'PO-{2020+i}' for i in range(4)],
            'duplicate_exact': ['INV-4100'], 'duplicate_fuzzy': ['INV-4101']}
    return files, gold

def workbook_sample():
    buffer = io.BytesIO()
    pd.read_csv(io.BytesIO(generate()[0]['inventory.csv'])).to_excel(buffer, index=False, sheet_name='Inventory')
    return buffer.getvalue()
