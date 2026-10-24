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

## Completion
The user selected George (`bm_george`) for the genuine Kokoro narration, supplied https://youtu.be/NclbnG0_8d0, and explicitly selected a public repository under Saifullahakjsnd (Saifullah). Authentication was verified as that exact account, the destination was checked before creation, and the repository was pushed to main at https://github.com/Saifullahakjsnd/QuietOps.

All eight public screenshots were fetched and hash-checked. The README embeds application screenshots and a labelled article preview; the DEV draft has five commit-pinned images, the real video embed, source links and measured results. Local media, offline review and the source/evidence archive are complete. The user then published the article manually at https://dev.to/saif-uk/i-built-a-local-ai-to-turn-a-shops-evening-spreadsheet-hunt-into-a-fix-queue-5b5p. The public article, challenge tags and embeds are verified; its actual screenshot is embedded in the GitHub README. The requested work is complete.
