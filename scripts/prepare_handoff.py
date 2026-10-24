"""Build local review artifacts; no account selection or external publishing."""
import hashlib
import html
import json
import re
from pathlib import Path
import markdown
from backend.demo import generate, workbook_sample

ROOT=Path(__file__).resolve().parents[1]

def main():
    fixtures=ROOT/'demo/fixtures';fixtures.mkdir(parents=True,exist_ok=True)
    files,gold=generate()
    for name,content in files.items():(fixtures/name).write_bytes(content)
    (fixtures/'inventory.xlsx').write_bytes(workbook_sample())
    labels=fixtures/'gold';labels.mkdir(exist_ok=True)
    (labels/'labels.json').write_text(json.dumps(gold,indent=2),encoding='utf-8')
    (fixtures/'README.md').write_text('# Explicitly fictional QuietOps fixtures\n\nGenerated with seed 42; scan date 2026-10-24. No real shop or personal information.\n\n60 SKUs, 12 suppliers, 90 sales days. CSV originals and a one-sheet inventory XLSX are included. Gold labels live separately under `gold/` and are not passed into detector or model inputs.\n\nRegenerate with `python -m scripts.prepare_handoff`.\n',encoding='utf-8')
    source=ROOT/'docs/DEV_SUBMISSION.md'
    content=source.read_text(encoding='utf-8')
    # Keep downloaded review packages usable without fetching hosted images.
    content=re.sub(r'https://raw\.githubusercontent\.com/Saifullahakjsnd/QuietOps/[0-9a-f]{40}/(demo/assets/screenshots/[^)\s]+)',r'../\1',content)
    body=markdown.markdown(content,extensions=['fenced_code','tables'])
    body=body.replace('{% youtube NclbnG0_8d0 %}', '<a href="https://youtu.be/NclbnG0_8d0">Watch the verified public YouTube demo</a>')
    body=body.replace('{% github https://github.com/Saifullahakjsnd/QuietOps %}', '<a href="https://github.com/Saifullahakjsnd/QuietOps">QuietOps on GitHub</a>')
    post_body=body[body.index('<p><em>This is a submission'): ]
    post_path=ROOT/'docs/POST_PREVIEW.html'
    if post_path.exists():
        post_prefix=post_path.read_text(encoding='utf-8').split('</header>',1)[0]+'</header>'
        post_path.write_text(post_prefix+post_body+'</main></body></html>',encoding='utf-8')
    preview='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QuietOps — local article review</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f4f6ef;color:#263d30;font:17px/1.8 system-ui,sans-serif}main{max-width:920px;margin:40px auto;background:white;border:1px solid #dce4d1;border-radius:14px;padding:45px 60px}h1,h2{font-family:Georgia,serif;font-weight:400;line-height:1.3}h2{font-size:31px;margin-top:42px}p{margin:18px 0}a{color:#366d4b;text-underline-offset:3px}img,video{max-width:100%;height:auto;border:1px solid #dce4d1;border-radius:9px}video{display:block;margin:22px 0;background:#182e23}pre{overflow:auto;background:#f1f5e8;padding:20px;border-radius:7px}code{font-size:.86em}aside{border-left:4px solid #90ad65;padding:15px 20px;background:#edf3e4;font-size:14px;margin:24px 0}.title{font-family:Georgia,serif;font-size:37px;line-height:1.3}.files{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}@media(max-width:640px){main{margin:0;padding:25px 22px;border-radius:0}.title{font-size:29px}}@media print{main{margin:0;border:0;padding:0}.review-player{display:none}h2{break-after:avoid}img{break-inside:avoid}}
    </style></head><body><main><div class="title">QuietOps: the local review package</div><aside>George narration is complete. The supplied YouTube video is verified. The public GitHub repository and all hosted screenshots are verified. The article is ready for user review and manual DEV publication. This offline preview uses the included local images.</aside><div class="review-player"><video controls preload="metadata" src="../demo/assets/video/final_demo.mp4"></video><div class="files"><a href="../dist/quietops-local-bundle.zip">Source and demo ZIP</a><a href="../demo/assets/audio/kokoro_voiceover.wav">George WAV</a><a href="../demo/assets/audio/subtitles.srt">SRT captions</a><a href="DEV_SUBMISSION.md">Article Markdown</a></div></div>'''+body+'</main></body></html>'
    (ROOT/'docs/DEV_SUBMISSION.html').write_text(preview,encoding='utf-8')
    srt=ROOT/'demo/assets/audio/subtitles.srt'
    if srt.exists():
        vtt='WEBVTT\n\n'+re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})',r'\1.\2',srt.read_text(encoding='utf-8'))
        srt.with_suffix('.vtt').write_text(vtt,encoding='utf-8')
    print('Prepared fictional fixtures, local article HTML, and browser captions.')

if __name__=='__main__':main()
