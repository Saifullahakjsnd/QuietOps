# QuietOps local handoff

The user selected George for narration, supplied the uploaded YouTube video, and chose GitHub owner Saifullahakjsnd (Saifullah). All local deliverables are complete. GitHub publication is now requested but awaits authenticated access for that account; public visibility is confirmed. No repository or DEV article has been published by this workflow.

## Open the result

- App: http://127.0.0.1:3002 while the launchers are running.
- Final video: `demo/assets/video/final_demo.mp4`.
- George master: `demo/assets/audio/kokoro_voiceover.wav`.
- Captions: `demo/assets/audio/subtitles.srt` and `subtitles.vtt`.
- Complete article text: `docs/DEV_SUBMISSION.md`.
- Offline article and video review: `docs/DEV_SUBMISSION.html`.
- Portable archive: `dist/quietops-local-bundle.zip`, with `dist/SHA256SUMS.txt`.
- User upload instructions: `docs/YOUTUBE_HANDOFF.md`.

## Verified

Nine backend tests passed; the original three browser tests exercised real inference, mapping/corrections and mobile navigation. TypeScript and production build passed. The final 118.12-second, 1920×1080 MP4 fully decodes and plays in Edge. All five screenshots embedded in the article preview load. Independent CPU ASR checks the actual George master and records the exact WAV hash. Measured WAV loudness: -16.1 LUFS integrated, -1.5 dBFS true peak, 2.6 LU loudness range.

Screen timings, voice/model hashes, actual generated speech durations, phrase cues and output checksums are in the media verification files. Captions stay within their corresponding recorded scenes; phrase timing is not claimed to be word-level forced alignment.

The demo and package fixtures are explicitly fictional. Code, documentation, synthetic fixtures and final evidence are packaged. The archive excludes model weights, all working shop databases/originals, virtual environments, caches, logs, `.env` files and raw recording intermediates.

## External handoffs

The article contains the verified public YouTube embed for https://youtu.be/NclbnG0_8d0. The selected GitHub destination owner is Saifullahakjsnd; public publication requires a signed-in connection for that exact account. After publication, replace local screenshots with verified repository-hosted URLs (or DEV image URLs for a private repository). The user reviews and publishes the DEV article. No nonexistent repository or screenshot URL is claimed.

Docker Compose configuration is provided, but container execution remains unverified because the Docker engine is unavailable. The native loopback deployment is verified and running. Other sessions' services were left separate.
