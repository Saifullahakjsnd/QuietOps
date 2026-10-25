"""Opt-in fictional companion history. Never changes the original seed-42 demo."""
import random
from datetime import timedelta
import pandas as pd
from .demo import AS_OF, SUPPLIERS

SEED = 35042

def generate():
    rng = random.Random(SEED)
    sales, history = [], []
    start = AS_OF - timedelta(days=329)
    # Ends before the existing demo's 90-day sales window, with no overlap.
    for i in range(60):
        sku, rate, lead = f'SKU-{i+1:03}', 2+i % 7, 5+i % 6
        for day in range(240):
            phase = (day + (i % 8)*7) % 56
            # Sustained rises, falls and occasional unsignalled shocks.
            multiplier = 1 if phase < 28 else (2 if phase < 35 else (8 if phase < 49 else 3))
            qty = max(0, round(rate * multiplier + rng.choice([-1, 0, 0, 1])))
            if rng.random() < .025:
                qty += rate * 5
            sales.append({'sku': sku, 'date': (start+timedelta(days=day)).isoformat(), 'qty': qty, 'unit': 'each'})
            if day >= 90 and day % 14 == 7:
                # Inventory policy samples a broad cover range. No future demand is used.
                on_hand = round(rate * lead * rng.choice([.5, 1.5, 3, 5, 9]))
                history.append({'sku': sku, 'date': (start+timedelta(days=day)).isoformat(),
                                'on_hand': on_hand, 'lead_days': lead,
                                'supplier': SUPPLIERS[i % 12], 'unit': 'each'})
    # Additional genuine input rows in the opted-in fictional scenario. Originals stay immutable.
    # Deliberately constructed live illustration: continue the companion's recurring
    # demand pattern for SKU-007. This scenario was chosen after model exploration;
    # it is not an independent performance test. Held-out historical data is unchanged.
    for days_ago in range(90):
        phase = (329-days_ago+42) % 56
        multiplier = 1 if phase < 28 else (2 if phase < 35 else (8 if phase < 49 else 3))
        sales.append({'sku': 'SKU-007', 'date': (AS_OF-timedelta(days=days_ago)).isoformat(),
                      'qty': 8*(multiplier-1), 'unit': 'each'})
    return {'predictive-sales.csv': pd.DataFrame(sales).to_csv(index=False).encode(),
            'stock-history.csv': pd.DataFrame(history).to_csv(index=False).encode()}
