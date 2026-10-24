# Evaluation

Run `.venv\Scripts\python.exe -m backend.eval.run_evaluation --real-ai` from the project root. It creates a temporary isolated workspace and writes machine-readable measurements to `docs/evaluation-results.json`.

## Recorded native run

2026-10-23 21:01 UTC (2026-10-24 in Karachi), Windows, 64 GB system RAM, RTX 4090, dedicated Ollama 0.40.8. Ministral 3 8B Q4_K_M, 4096-token context; digest `1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71`.

| Detector | True positives | False positives | False negatives | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stock cover | 6 | 0 | 0 | 1.00 | 1.00 |
| Late orders | 4 | 0 | 0 | 1.00 | 1.00 |
| Exact invoice candidate | 1 | 0 | 0 | 1.00 | 1.00 |
| Fuzzy invoice candidate | 1 | 0 | 0 | 1.00 | 1.00 |

5,522 valid rows; 12 candidates; deterministic scan 72 ms; generation/import/mapping/scan 342 ms. Four real AI calls passed schema/source/numeric checks, with measured generation path latencies of 1,916 / 1,360 / 1,497 / 1,583 ms respectively. These are warm, single-example measurements, not throughput or tail-latency benchmarks. Model text still has semantic imperfections: one stock review step says “avoid duplicate invoices” where “avoid duplicate orders” is more appropriate. This is why human editing remains necessary.

An earlier repeat run rejected one invented evidence ID. The rejection is preserved in `evaluation-guard-rejection.json`; the response was not shown as a valid explanation. The schema now constrains decoded evidence IDs to the actual issue sources in addition to post-generation validation. The final passing measurements are in `evaluation-results.json`.

Backend: nine tests passed, including extreme numeric/subcent rejection. Browser: three tests passed, including real model inference and approval/export, explicit CSV mapping/correction, and eight-view mobile navigation without horizontal page overflow; mobile navigation passed again after readability and stable accessible-name improvements. TypeScript, production build, production dependency audit, and Compose configuration validation passed. Native execution is verified; Docker containers have not been built or run.

The reproducible seed uses a fictional 60-product, 12-supplier shop with 90 days of sales and separately generated gold labels. Expected issue subjects: six low-cover SKUs, four overdue purchase orders, one exact invoice group and one fuzzy invoice pair. Gold labels are not passed to the detector or model. Report precision/recall, false positives and false negatives per kind from the output, not from expected values alone.

The optional real-AI run calls the actual local Ollama model on one issue per detector kind. It records model digest, latency, text and source IDs, with schema/source/numeric guard outcomes. This is a small integration check, not an independent semantic hallucination benchmark. No fake model response is used in this evaluation. The approval unit test contains an explicitly labelled fixture to isolate decision behavior.

Backend tests check stock-cover arithmetic against source quantities, all contributing row membership, XLSX round trip, immutable originals, invalid numeric/date quarantine, mismatched units, future-date exclusion, stale approval prevention and hallucinated source/number rejection. Browser tests exercise actual demo loading, source evidence, real inference, approval and export, explicit mapping, a correction proposal, navigation and mobile overflow.

Measurements from a run are hardware- and load-dependent. An independently running session can share GPU/CPU resources. Detector performance on this intentionally controlled fixture is not evidence of accuracy on messy real shops. No measured human time savings are claimed. A defensible future field evaluation would use held-out real data with owner adjudication and timed manual vs assisted review.

## Finished media verification

The final narrated MP4 is 118.12 seconds at 1920×1080, with H.264 video, AAC mono narration, and English captions burned into a reserved strip below the full application image. The separate master WAV is 24 kHz, with SRT and WebVTT captions provided. Narration is genuine Kokoro-82M v1.0 via kokoro-onnx 0.6.1, using the user's explicit George / `bm_george` choice. The actual model and voice-pack hashes are in `demo/assets/video/final-verification.json`.

Thirteen speech scenes are anchored to observed changes in the original recording; screen timing is unchanged. Maximum pitch-preserving speech tempo adjustment is approximately 1.16×. Thirty-one phrase cues fit the scene windows. Cue timings are proportional to phrase word counts within each measured speech segment, not claimed forced word alignment.

FFmpeg fully decodes the finished file. Edge/Playwright verified 1920×1080 metadata, actual playback advancing beyond one second with decoded frames, and zero browser errors. Actual frames at source evidence, AI explanation, review and approval were inspected for caption placement. The offline article loaded all five embedded screenshots. These checks are recorded in `demo/assets/video/playback-verification.json`.

An independent CPU-only faster-whisper tiny.en transcription recovered the narration's core statements, including the synthetic shop counts, oat-milk quantities, approval boundary, and qualified payoff. Rough token-sequence similarity was 0.966; digit/word normalization and ASR errors affect that number. It is a speech-continuity/content check, not a claim of perfect pronunciation or human listening review. The transcription report is bound to the exact final WAV hash in `demo/assets/audio/transcript-qa.json`.
