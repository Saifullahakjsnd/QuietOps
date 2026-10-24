# Completed demo and reproducible production

The final video is `demo/assets/video/final_demo.mp4`: **118.12 seconds, 1920×1080, H.264/AAC**, genuine Kokoro-82M **George (`bm_george`)** narration selected by the user, and English captions. The full source application image is scaled into a frame with a dedicated caption strip so subtitles do not obscure evidence or controls. Separate WAV, SRT and WebVTT files are in `demo/assets/audio/`.

All shop data is explicitly fictional. The screen recording uses the actual browser, backend and local Ministral inference. No fabricated UI or simulated model output is used. Original screen timing is preserved.

## Story and actual scenes

| Source-video interval | Visible story |
| --- | --- |
| 0–11 s | Empty workspace: the evening spreadsheet burden |
| 11–20 s | Select fictional shop; twelve candidates appear |
| 20–26 s | Retained originals, hashes and confirmed mappings |
| 26–35 s | Lowest stock cover against supplier lead time |
| 35–39 s | Short issue inbox |
| 39–48 s | Oat-milk arithmetic, source cells and contributing sales rows |
| 48–57 s | Explicit assumptions and genuine local inference |
| 57–69 s | Actual Ministral explanation and suggested next step |
| 69–75 s | Purchase review draft |
| 75–85 s | Review dialog with editable wording |
| 85–96 s | Approval and manual export; no external financial action |
| 96–103 s | Audit trail |
| 103–118 s | One approved draft, with the synthetic payoff qualified |

The record of a simulated review/approval is confined to a separate fictional recording workspace. Regular user data is not modified by recording. Manual upload/mapping/correction is covered separately by the browser tests. The final narration asks the reviewer to edit where needed; the captured interaction inspects and approves the draft without a text edit.

## Record again

1. Start the frontend and dedicated local model as described in README.
2. Stop only the verified QuietOps backend, then start `scripts/backend-record.ps1`; it creates a fresh timestamped recording workspace.
3. Run `npm run demo:record`. `demo/record_demo.ts` captures real inference, sources, a proposal, approval, export and audit history. Raw WebM files are ignored by Git.
4. Inspect the new recording's actual scene changes. Update `demo/assets/audio/narration-scenes.json`, including its video hash. The current plan is bound to the current 118.12-second silent MP4 and must not silently be reused after a different capture.
5. Install optional `demo/requirements-narration.txt` and prepare actual model assets with `python demo/prepare_narration.py`. The final voice has been explicitly selected: run `python demo/finish_video.py --voice bm_george`.
6. The script generates each narration scene with genuine Kokoro, modestly adjusts speech tempo if needed, normalizes the master, creates phrase captions and renders the final MP4. No final voice is chosen by a default argument.
7. Optional independent speech QA: install `demo/requirements-qa.txt`, then run `python demo/verify_narration.py`. Render the article/fixtures with `python -m scripts.prepare_handoff`; verify playback with `npx tsx demo/verify_playback.ts`.
8. Build the source/evidence archive with `python -m scripts.package_release`. Restart the regular backend after recording so the recording approvals stay isolated.

## Verified evidence

- `video/recording-report.json`: original capture dimensions, duration, genuine inference and zero browser errors.
- `video/final-verification.json`: scene times, tempo, model hashes, final output hashes and full decode result.
- `video/playback-verification.json`: actual Edge playback and all five article screenshots loading.
- `audio/transcript-qa.json`: independent CPU transcription, bound to the exact final WAV hash. ASR is not a human listening review.
- `audio/narration_script.md`: final spoken text.
- `audio/narration-scenes.json`: source-scene plan and silent-video hash.
- `audio/subtitles.srt`: 31 English phrase cues. Timing is scene-anchored, not claimed word-for-word forced alignment.

The user supplied the real YouTube video at https://youtu.be/NclbnG0_8d0; its oEmbed metadata resolves to “QuietOps” and the article contains the actual DEV embed. The source and screenshots are published at https://github.com/Saifullahakjsnd/QuietOps under the user-selected account. All eight hosted image URLs were verified, and the article uses five commit-pinned images. The user published the reviewed DEV article manually at https://dev.to/saif-uk/i-built-a-local-ai-to-turn-a-shops-evening-spreadsheet-hunt-into-a-fix-queue-5b5p.
