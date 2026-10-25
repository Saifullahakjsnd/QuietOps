# GitHub-hosted video for the updated DEV post

The owner requested keeping the new video on GitHub instead of uploading another YouTube video. This supersedes the earlier YouTube handoff for the current edition. The original published article and original YouTube video remain intact.

## Prepared result

- [Full narrated MP4: 2:24, 1080p](https://raw.githubusercontent.com/Saifullahakjsnd/QuietOps/0fae4c95149991c28abf4c66c727880dd6c9db8d/demo/assets/tabpfn/final/video/final_demo.mp4)
- [Muted inline excerpt: 12 seconds, 720p](https://raw.githubusercontent.com/Saifullahakjsnd/QuietOps/3ef2f835e4cbc8be82c29ddaef584a3271765007/demo/assets/tabpfn/final/video/post-preview.mp4)
- [Publication-ready post body](DEV_SUBMISSION_FINAL.md)
- [Title, tags, verified image URLs and video metadata](DEV_PUBLISHING_META.json)
- [Offline preview](DEV_SUBMISSION_TABPFN.html)

The DEV body includes a native HTML `<video>` with a typed MP4 `<source>`, a poster image, and a prominent full-video link. Forem's current frontend treats raw HTML video as a muted loop and removes controls, so the inline clip is explicitly a silent preview. Full George narration and English captions are in the linked MP4. Opening that link may download the video for the reader's own player.

## Verification and limits

The public full-video and preview bytes were checked against local hashes. Microsoft Edge/Playwright successfully played the full public MP4 with controls and audio unmuted. The excerpt also played with the current upstream Forem GIF-video behavior applied locally: muted, looping, without controls. See [the playback report](../demo/assets/tabpfn/final/video/github-playback-verification.json).

GitHub raw serves these MP4s as `application/octet-stream`; using `<source type="video/mp4">` worked in the tested browser. The explicit watch/download link is retained as a fallback. This checks the browser and published Forem source; it does not claim that the existing live DEV article has been updated or that its live preview has been tested. Check the DEV editor's preview before publishing.

Primary implementation references checked on 2026-10-25:

- [Allowed video/source tags and attributes](https://github.com/forem/forem/blob/main/app/services/markdown_processor.rb)
- [Video handling in the HTML parser](https://github.com/forem/forem/blob/main/app/services/html/parser.rb)
- [Frontend GIF-video behavior](https://github.com/forem/forem/blob/main/app/javascript/utilities/gifVideo.js)
- [DEV editor guide](https://dev.to/p/editor_guide)

## Regenerate the final post

```powershell
.venv\Scripts\python.exe -m scripts.prepare_predictive_post --assets-commit 0fae4c95149991c28abf4c66c727880dd6c9db8d --github-video --preview-commit 3ef2f835e4cbc8be82c29ddaef584a3271765007
```

The command verifies five hosted screenshots, the complete video and the excerpt, then writes the final body and offline preview. It does not publish or update DEV. `update.txt` requires approval before changing the existing published article.
