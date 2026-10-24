# QuietOps implementation plan

Build a local-first operational review application in this folder only. Other sessions are active: do not stop their processes, change global configuration, or reuse their ports.

## Chosen runtime
- Next.js / TypeScript / Tailwind / shadcn-style Radix components, port 3002.
- FastAPI / Pandas / DuckDB / SQLite, port 9002, project-local virtual environment and data directory.
- Ministral 3 8B through a dedicated Ollama server at 127.0.0.1:11436. User requested a stronger alternative to Qwen/Phi. Apache 2.0 license verified in the official Mistral model card. Use a 4096-token context and one inference at a time.

## P0 vertical slice first
1. Seed explicitly fictional 60-SKU, 12-supplier, 90-day shop data with separate ground truth.
2. Parse CSV/XLSX; preview and confirm mappings, date convention, currency and units.
3. Quarantine invalid rows and preserve file / sheet / row / cell lineage.
4. Deterministically detect stock cover, late partial orders, and exact/fuzzy duplicate invoice candidates.
5. Explain evidence with real local inference, validate cited IDs and numbers, and show genuine failure states.
6. Review a proposed action, explicitly approve it, export a draft. Never send or alter financial records.
7. Test numeric correctness, lineage, XLSX, approval, and real inference before broadening views.

## Complete application
Dashboard, imports, quality review, issue inbox, fix queue, inventory, suppliers, audit history. Responsive accessible interface with visible model and dataset status. Local persistence and separate correction export. Tests, reproducible evaluation, architecture, setup instructions, Docker Compose, and actual screenshots / demo recording.

## Publication boundaries
Build and verify locally first. GitHub destination/account, narration voice, YouTube handoff and external publication require the explicit checkpoints in BUILD_PROMPT.md. Do not invent assets, links, results, or publish anything automatically.

## User updates and local completion
The user selected George (`bm_george`) for narration; the local video, captions, article, offline preview and source/evidence archive are complete. The user subsequently supplied the real YouTube URL `https://youtu.be/NclbnG0_8d0` and selected GitHub owner `Saifullahakjsnd`, display name Saifullah, reopening GitHub publication after previously excluding it. Confirm repository visibility and authenticated access for this exact account before external repository creation or push. No repository link or hosted screenshot URL may be invented.

The user confirmed **public** visibility and asked for screenshots embedded in GitHub. Prepare a public QuietOps repository under Saifullahakjsnd, with actual app screenshots in the README, an explicitly labelled local article-preview screenshot, and repository-hosted image URLs for the DEV post. The remaining prerequisite is authenticated access for the selected account; no further visibility approval is needed.
