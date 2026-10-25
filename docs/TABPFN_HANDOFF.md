# TabPFN upgrade handoff

The updated app runs at **http://127.0.0.1:3002** with an independent fictional workspace at `data/tabpfn-final-film`. The original shop database, published DEV source and original screenshots/video were preserved. The user-approved upgrade and narrated demonstration were pushed to the existing public repository at commit `0fae4c95149991c28abf4c66c727880dd6c9db8d`; the hosted MP4 and five post screenshots were verified against local hashes. The live DEV article is unchanged.

Open **Looking Ahead** to inspect the actual model results. SKU-007 is a constructed recurring-demand example: TabPFN estimates 84.2% risk while both baselines show cover. Its genuine local Ministral explanation and an edited supplier-review draft approved for manual export are retained. The example was selected after model exploration and is explicitly labelled accordingly.

The new narrated final edition is [143.76 seconds, 1920?1080, with genuine George narration and English captions](../demo/assets/tabpfn/final/video/final_demo.mp4). The earlier short captioned clip below is retained as supplemental evidence.

## Deliverables

- [Model setup, license acceptance and access](TABPFN_SETUP.md)
- [Data audit, leakage controls, temporal split and limitations](TABPFN_EVALUATION.md)
- [Actual historical evaluation JSON](tabpfn-evaluation.json) and [current prediction evidence](tabpfn-live-predictions.json)
- [43-second captioned workflow video](../demo/assets/tabpfn/looking-ahead-demo.mp4), [screenshots](../demo/assets/tabpfn/02-looking-ahead.png), [comparison](../demo/assets/tabpfn/07-comparison.png), and [approved supplier-review export](../demo/assets/tabpfn/approved-supplier-review.md)
- [Demo walkthrough](TABPFN_DEMO.md) and reproducible recorder via `npm run demo:predictive` in an empty isolated workspace
- [Final post for review](DEV_SUBMISSION_FINAL.md) and [GitHub video publication guide](VIDEO_PUBLICATION.md), prepared locally for review; the published post was not updated
- [Verification record](tabpfn-verification.json): 18 backend tests, three existing browser tests, the new real-model recording, TypeScript checking, production build, dependency check, full video decode and desktop/mobile inspection passed

The historical comparison uses 420 training and 240 later test examples. TabPFN precision/recall/F1: **100.0% / 94.5% / 97.2%**. Cover-rule F1: **64.7%**; recent-demand F1: **71.8%**. These measured synthetic results do not establish real-shop accuracy, calibrated business risk, prevented losses or saved time.

## Runtime notes

The backend launcher inherited license acceptance for this local demo and the independent data path. A normal restart uses the launcher's process environment; follow the setup guide to select this same workspace again. Optional model weights are gitignored under `data/models/` and cached by Hugging Face. No weights or credentials are committed.

The adapter pins and verifies TabPFN-3.5, exposes disabled/error states and never substitutes another model's probabilities. It materializes a regular safetensors file to avoid an upstream cache-symlink format-detection issue. The Next.js proxy now permits the backend's local inference timeout, including cold Ministral startup. Grounding failures remain blocked; the prompt requests explicitly uncertain wording.

Predictive drafts become stale when mapped data or the scan date changes. Their explanation, approval and export endpoints recheck current input fingerprints. The deterministic inbox and original calculations remain separate.

The owner chose to keep the new media on GitHub. The DEV body embeds a short muted preview and links the full narrated MP4. YouTube is optional; the live DEV update still awaits separate approval.
