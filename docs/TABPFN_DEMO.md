# Looking Ahead demo

Use an independent fictional workspace and the existing local Ministral server. Keep the original narrated video and published article intact.

1. Open Overview and show the original synthetic shop's deterministic stock, delivery and invoice findings. These remain the issue inbox's source of truth.
2. Open Looking Ahead. Explain why one current inventory snapshot cannot train a historical predictor. Click **Load predictive example**; inspect its two synthetic source files under Import & mapping. Originals remain downloadable.
3. Click **Run TabPFN prediction** and wait. This is actual local TabPFN-3.5 inference. A failure must remain visible; never narrate an unrun estimate as real.
4. Show the earlier-training/later-test split, outcome cutoff and measured comparison against both the existing cover rule and seven-day baseline. Acknowledge where a simpler baseline performs better.
5. Inspect SKU-007 if the actual model flags it beyond the rule. Show recent sales, stock cover, lead time, the unchanged stock snapshot, both sales sources and uncertainty. Its score describes no-incoming-receipt risk, not certainty of a future physical stockout.
6. Click **Explain with local AI**. Ministral explains supplied TabPFN facts; it cannot create the probability. Guard failures withhold text and draft creation.
7. Click **Create action draft**. Edit the supplier-review request in Fix queue; approve for export. Export produces a manual-follow-up draft. Nothing is sent or purchased.
8. Change the scan date or confirm new mapped data; show that predictive drafts become stale and cannot be approved/exported until predictions and review are refreshed.

Screenshots and any new recording should use `demo/assets/tabpfn/`, keeping the original published demonstration assets unchanged. `demo/record_predictive.ts` records the real app journey and retains model/approval evidence separately.
