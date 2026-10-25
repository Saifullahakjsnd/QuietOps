# Updated demo publication

The owner supplied the new YouTube upload: [quiet-ops-final](https://youtu.be/yvtDUqRYet8). YouTube oEmbed returned a video entry and an iframe for this ID. The final DEV post now uses its supported YouTube embed:

```liquid
{% youtube yvtDUqRYet8 %}
```

Copy [the final post body](DEV_SUBMISSION_FINAL.md) into the DEV editor and check Preview before saving. The owner is editing DEV manually; this workflow has not changed the live article. [Title, tags and verified asset metadata](DEV_PUBLISHING_META.json) accompany the body.

The earlier GitHub HTML-video approach did not establish successful embedding in DEV. Its local checks only verified browser playback and upstream Forem behavior. The YouTube embed replaces that preview and its download instructions in the final article. The [full narrated GitHub MP4](https://raw.githubusercontent.com/Saifullahakjsnd/QuietOps/0fae4c95149991c28abf4c66c727880dd6c9db8d/demo/assets/tabpfn/final/video/final_demo.mp4) remains available separately.

## Regenerate the final post

```powershell
.venv\Scripts\python.exe -m scripts.prepare_predictive_post --assets-commit 0fae4c95149991c28abf4c66c727880dd6c9db8d --youtube-url https://youtu.be/yvtDUqRYet8
```

The command verifies five hosted screenshots and YouTube oEmbed, then writes the final body, metadata and offline preview. It does not publish or update DEV. The original edition and original YouTube video remain preserved.
