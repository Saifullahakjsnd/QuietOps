# Predictive evaluation methodology

## Data audit

The original fictional shop has 60 inventory rows, 5,400 sales rows (90 days), 24 order lines and 38 invoices. There is only one current inventory snapshot and one cumulative order snapshot. Gold labels test deterministic fixture expectations; they are not training features or predictive outcomes. SQLite stores immutable originals, mapped valid rows, quarantined data, evidence, explanations, drafts and decisions.

Those files alone cannot supply historical stockout outcomes. `backend/predictive_demo.py` therefore adds an **opt-in synthetic** companion, seed 35042: 240 earlier days of sales per product, dated stock snapshots, and 90 supplemental sales rows for SKU-007. The earlier sales end before the original 90-day window begins. They include rising, falling and occasional shock demand, and stock levels selected without future sales. This does not reconstruct real history or prove commercial value.

The recent example preserves SKU-007's original stock snapshot and original sales file. A separate source file supplies additional fictional transactions over the original 90-day window. They continue the historical recurring demand pattern: both the 90-day rule and seven-day baseline can show cover before the next synthetic demand phase. The live illustration was selected after exploring model outputs; it is not an independent test. The first, isolated seven-day surge was not flagged by TabPFN, and longer isolated plateaus were not flagged either. The held-out historical rows and their metrics were not changed during this exploration. Inspect the actual model estimate after inference; a designed scenario is not proof the model will catch it.

## Target and as-of features

Target: the sum of **observed sales** after an end-of-day stock snapshot and through its supplier lead-time window exceeds that snapshot's stock, assuming no incoming receipt. This is a counterfactual demand-exceeds-stock label, not an independently observed physical stockout or a supplier-failure label. Lost sales, actual replenishment and changing lead times are unobserved.

Features use only rows on or before the snapshot: on hand, lead days, average daily sales over the observed trailing window (up to 90 calendar days), 28/7-day daily rates, recent-to-28-day ratio, 28-day volatility, and cover using trailing/recent rates. Sales missing inside the feature window count as zero, matching the existing deterministic assumption. Current inventory is not used to create historical examples. SKU, item text, supplier identity, future sales, labels and gold fixture annotations are excluded from the feature matrix. Supplier lead time is the usable supplier information.

Outcome sales are accessed separately, only to label mature examples. Every day in a labelled outcome window needs compatible observed sales (explicit zeros allowed). Quarantined rows never enter features or labels. Evidence links include immutable source files, source-row lists, dates and quantity aggregates.

## Split and comparison

Select a cutoff at 65% of unique snapshot dates. Training includes only examples whose **outcome end is strictly before** that cutoff; held-out examples start at or after it. Purge any boundary-overlapping examples. Require at least 40 training and 20 held-out examples, at least four dates, and both outcomes in each split. Held-out outcomes never enter the model fit. The same fitted model supplies held-out scores and current SKU estimates; it is not refitted on held-out labels for the demo.

Three methods are scored on identical later examples:

1. TabPFN-3.5, fixed two-estimator configuration and 0.50 review threshold.
2. The existing stock-cover predicate: trailing observed cover is less than supplier lead time.
3. A simple recent-demand baseline: last-seven-day daily rate times lead time exceeds stock.

Report precision, recall, F1, accuracy and confusion counts; TabPFN also receives Brier score, ROC AUC and average precision. The recent baseline may be competitive or better; report its measured result. No threshold tuning or feature search uses held-out outcomes. An individual model score has no claimed calibration or confidence interval. Repeated SKUs and related synthetic time patterns reduce independence; no IID error bars are asserted.

## Results and interpretation

The real CPU run used the pinned TabPFN-3.5 checkpoint and produced these results on 240 held-out rows (420 training rows):

| Method | Precision | Recall | F1 | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| TabPFN-3.5 | 1.0000 | 0.9450 | 0.9717 | 0.9750 |
| Existing stock-cover rule | 0.5909 | 0.7156 | 0.6473 | 0.6458 |
| Recent-demand baseline | 0.7629 | 0.6789 | 0.7184 | 0.7583 |

TabPFN confusion counts: TP 103, FP 0, FN 6, TN 131. Brier score 0.026396, ROC AUC 0.989985, average precision 0.990719. It caught 30 held-out positive examples missed by the cover rule. Latest training outcome: 2026-06-02; first test date: 2026-06-06; latest test outcome: 2026-07-28. No fixture rows needed boundary purging; the regression suite exercises a boundary that does need purging.

Actual outputs belong in [the machine-readable evaluation](tabpfn-evaluation.json). Its `model.inference_ran`, checkpoint SHA-256, fixture hashes, chronological boundaries, individual held-out labels/scores and comparison metrics distinguish a successful real run from software tests. No result is substituted if installation, checkpoint access, memory or inference fails.

This is one temporal holdout from a deliberately synthetic generator. It does not establish generalization to another shop, true stockout frequency, calibrated business risk, prevented loss, or saved time. Real evaluation needs independently collected dated stock/receipt history, longer temporal folds and deployment-specific calibration. The original deterministic evaluation and published article are preserved.
