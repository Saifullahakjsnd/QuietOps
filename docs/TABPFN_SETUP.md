# Optional TabPFN-3.5 setup

QuietOps keeps the existing Next.js/FastAPI/Pandas/DuckDB/SQLite application. TabPFN is an optional, local binary classifier. Deterministic scans work without it. No Gemma, purchasing, outreach or financial-record updates were added.

## Verified upstream information (2026-10-25)

- Package: `tabpfn==9.2.0`; Python 3.10+ upstream (this project uses Python 3.12).
- Explicit model: `ModelVersion.V3_5`, **TabPFN-3.5 base**, not the Fast, v3, v2 or cloud model.
- Official repository: `Prior-Labs/tabpfn_3_5`; revision `b0662010dd17679509f42326e2f9ba37a6f58818`.
- Checkpoint: `tabpfn-v3.5-20260909.safetensors`, 876,027,932 bytes. Each successful run records its SHA-256, package and PyTorch versions, device, seed, ensemble size and inference duration.
- Upstream supports classification and regression. QuietOps uses binary classification and `predict_proba`.
- Upstream recommends a GPU with about 8 GB VRAM, with more memory needed for larger data. CPU use is supported for moderate data; upstream's default CPU sample guard for this release is 5,000. QuietOps limits training and prediction batches to 2,000 rows each and uses two estimators, seed 42, and at most eight CPU threads. File size is not runtime memory: allow multiple GB of free RAM and measure on your own workload. This machine has 64 GB RAM; CPU was selected because the GPU was occupied.

Sources: [official installation and usage](https://github.com/PriorLabs/TabPFN), [model capabilities](https://docs.priorlabs.ai/models), [model card and files](https://huggingface.co/Prior-Labs/tabpfn_3_5), [PyPI](https://pypi.org/project/tabpfn/9.2.0/).

## License and access

Code and model weights have separate licenses. Read the [TabPFN-3.5 non-commercial, non-production license](https://huggingface.co/Prior-Labs/tabpfn_3_5/blob/main/LICENSE) before enabling model use. Commercial or production deployment needs an appropriate license from Prior Labs. This integration does not grant model rights under QuietOps' repository license.

The project owner explicitly accepted the model license in the development conversation for this local non-commercial hackathon demonstration on 2026-10-25. That acceptance was recorded only in the local SQLite workspace, not as acceptance for other users. For another workspace, set the following process environment variable **only after accepting the license yourself**:

```powershell
$env:QUIETOPS_TABPFN_LICENSE_ACCEPTED = 'yes'
```

The adapter uses upstream's documented manual model-download approach: it obtains the public checkpoint with `huggingface_hub` at the pinned revision, checks SHA-256 `ece4d67eadfea42eb0e610df5189bea60cb7f31073d81e9c7a019b76eacf0be3`, and passes a regular local file path explicitly. Downloads use the normal Hugging Face cache, outside the repository, then materializes a regular safetensors file under the gitignored `data/models/` directory. This works around upstream 9.2.0 resolving cache symlinks to extensionless blobs and selecting the wrong loader. Both cached copies together use about 1.8 GB disk space. Network access is needed for the first download; shop tables are passed to local inference. If the provider requires authentication, accept its terms through the official account interface and configure its token locally. Never commit tokens. Access errors are shown; no alternate predictor supplies TabPFN-labelled scores.

## Install and launch

From the project root, after installing the existing backend dependencies:

```powershell
# CPU avoids competing with an existing GPU model session.
.venv\Scripts\python.exe -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\python.exe -m pip install -r backend/requirements-tabpfn.txt
$env:QUIETOPS_TABPFN_DEVICE = 'cpu'
$env:QUIETOPS_TABPFN_LICENSE_ACCEPTED = 'yes' # only after your own acceptance
powershell -NoProfile -File scripts/backend.ps1
```

For CUDA, install the appropriate official PyTorch build instead and set `QUIETOPS_TABPFN_DEVICE=cuda` in that backend process. Do not unload other sessions' models. `QUIETOPS_TABPFN_ENABLED=0` disables inference. Status distinguishes disabled, license required, missing package, ready-to-attempt and inference error. Ready does not assert a checkpoint has run. Successful results record `inference_ran: true`.

Open **Looking Ahead** in the existing app. Load the original fictional shop if needed, then **Load predictive example** and **Run TabPFN prediction**. Loading the companion preserves the original demo files and decisions, adds two clearly fictional source files, and reruns the deterministic check. It is refused for workspaces containing non-synthetic data. No probability is shown before successful inference.

## Historical input contract

Import CSV/XLSX through the existing mapping confirmation and quarantine flow. Select `stock_history` for columns:

```csv
sku,date,on_hand,lead_days,supplier,unit
SKU-007,2026-03-01,224,5,Meadow Mills,each
```

Each SKU/date is an end-of-day snapshot; stock, supplier and lead time must have been known then. Add compatible daily sales, including explicit zero-sale rows across every labelled future window. Duplicate history keys across files stop evaluation. Current inventory is **never** reconstructed backwards. Missing outcome days, immature horizons, unit mismatches and fewer than 28 observed feature dates exclude examples and are recorded. Fractional lead times round up to whole days for outcome observation; the cover rule retains the supplied lead time.

The original order table has cumulative received quantity and a promised date but no order-created, receipt-event or historical availability timestamps. Using today's late/received flags for past snapshots would leak information. Supplier lead time is used, while supplier performance and incoming receipt adjustments are intentionally unavailable pending properly dated history.

## Reproduce and verify

```powershell
$env:QUIETOPS_TABPFN_LICENSE_ACCEPTED = 'yes'
.venv\Scripts\python.exe -m backend.eval.run_predictive_evaluation --data-dir data/tabpfn-evaluation-new
.venv\Scripts\python.exe -m pytest backend/tests -q
npm run typecheck
npm run build
```

Use an empty evaluation directory: the command refuses to erase existing datasets. It imports both fixture generators, runs real inference, writes `docs/tabpfn-evaluation.json` plus current predictions, and retains the independent SQLite workspace and original files. Repeated runs can differ slightly across hardware/library builds; seeds, fixed feature order, fixture file hashes and the training-content digest make inputs inspectable. Tests use an explicitly labelled fake adapter only for workflow assertions; they are not evidence that a real model ran.

To inspect the saved evaluation in the app, launch the backend with `QUIETOPS_DATA` pointing to that evaluation directory, then start the existing frontend and dedicated Ollama server. Keep the normal shop's data directory intact. See [evaluation methodology](TABPFN_EVALUATION.md) and [demo](TABPFN_DEMO.md).
