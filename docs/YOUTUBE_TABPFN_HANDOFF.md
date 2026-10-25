# Updated video upload handoff

The original YouTube video and published DEV article remain intact. This is a new narrated edition for the TabPFN upgrade.

## Upload this file

`G:\Hacktoberfest-2026-Week3\02-QuietOps\demo\assets\tabpfn\final\video\final_demo.mp4`

The MP4 is **143.76 seconds, 1920×1080**, H.264 video with AAC narration from genuine Kokoro-82M, using the previously selected George (`bm_george`) voice. English captions are burned into a strip below the application. The separate accessibility captions are `demo/assets/tabpfn/final/audio/subtitles.srt`.

Upload as Public or Unlisted to your chosen YouTube account and provide the new URL. The original video ID must not be reused to imply it contains this new walkthrough. No account is selected and no upload is performed automatically.

## Suggested title

QuietOps: Local TabPFN-3.5 Predictions, Evidence, and Human Approval

## Ready-to-paste description

The shop is closed. The spreadsheets are still open.

QuietOps turns shop spreadsheets into a source-linked review queue. This updated demo adds genuine local TabPFN-3.5 predictions alongside the original stock-cover, delivery and invoice checks. Local Ministral 3 8B explains supplied facts, and a person edits and approves a supplier-review draft for manual export.

Every shop record is fictional. The current recurring-demand illustration was selected after exploring model outputs; it is not an independent test. The separate chronological synthetic evaluation uses 420 training and 240 later test examples. TabPFN F1: 97.2%; existing cover rule: 64.7%; seven-day baseline: 71.8%. These results do not establish real-shop accuracy, calibrated business risk, prevented losses, or saved time.

Nothing is sent, ordered, or paid automatically. Model estimates assume no incoming receipt; evidence, uncertainty and stale-draft controls remain attached.

Source and reproducible evaluation: https://github.com/Saifullahakjsnd/QuietOps

Built with Next.js, FastAPI, Pandas, DuckDB, SQLite, TabPFN-3.5, and local Ollama/Ministral. Genuine Kokoro-82M George narration, Playwright capture, and FFmpeg encoding. TabPFN weights have separate non-commercial, non-production terms; see the repository's setup guide.

## After upload

Once the user supplies the actual new URL, verify its YouTube oEmbed response. After the approved GitHub push, run:

```powershell
.venv\Scripts\python.exe -m scripts.prepare_predictive_post --assets-commit ACTUAL_PUSHED_COMMIT --youtube-url ACTUAL_NEW_YOUTUBE_URL
```

That verifies the hosted screenshots against their local hashes, inserts the real DEV YouTube embed, and writes `docs/DEV_SUBMISSION_FINAL.md` plus publication metadata. The current `docs/DEV_SUBMISSION_TABPFN.md` is the editable review source. Publishing the existing DEV article's update remains a separate owner action.
