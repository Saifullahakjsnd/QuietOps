"""Render the reviewed post; verify real hosted assets and a user-supplied video URL."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import httpx
import markdown

ROOT=Path(__file__).resolve().parents[1]
REPO='Saifullahakjsnd/QuietOps'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--assets-commit',help='Already-pushed commit containing the actual new assets.')
    parser.add_argument('--youtube-url',help='Actual new URL supplied by the uploader; no automatic upload.')
    args=parser.parse_args()
    source=(ROOT/'docs/DEV_SUBMISSION_TABPFN.md').read_text(encoding='utf-8')
    title=re.search(r'^Title: (.+)$',source,re.M).group(1)
    tags=[t.strip() for t in re.search(r'^Tags: (.+)$',source,re.M).group(1).split(',')]
    body=source[source.index('*This is a submission'):]
    verified_images=[]
    if args.assets_commit:
        if not re.fullmatch(r'[0-9a-f]{40}',args.assets_commit):
            raise ValueError('Use a complete real commit SHA.')
        for target in dict.fromkeys(re.findall(r'!\[[^\]]*\]\((\.\./[^)]+)\)',body)):
            local=(ROOT/'docs'/target).resolve()
            relative=local.relative_to(ROOT).as_posix()
            url=f'https://raw.githubusercontent.com/{REPO}/{args.assets_commit}/{relative}'
            response=httpx.get(url,timeout=30,follow_redirects=True)
            response.raise_for_status()
            digest=hashlib.sha256(local.read_bytes()).hexdigest()
            if hashlib.sha256(response.content).hexdigest()!=digest:
                raise ValueError('Hosted screenshot bytes do not match: '+relative)
            body=body.replace(target,url)
            verified_images.append({'file':relative,'url':url,'sha256':digest,'http_status':response.status_code})
        def hosted_link(match):
            target=match.group(1)
            relative=(ROOT/'docs'/target).resolve().relative_to(ROOT).as_posix()
            url=f'https://github.com/{REPO}/blob/{args.assets_commit}/{relative}'
            return ']('+url+')'
        body=re.sub(r'\]\(([^):\n]+\.md)\)',hosted_link,body)
        body=body.replace('The updated local edition is prepared for the existing repository; its publication is a separate review step.',
                          'The updated implementation and demonstration assets are published in the linked repository.')
    video=None
    if args.youtube_url:
        parsed=urlparse(args.youtube_url)
        if parsed.hostname in ('youtu.be','www.youtu.be'):
            video_id=parsed.path.strip('/').split('/')[0]
        elif parsed.hostname in ('youtube.com','www.youtube.com','m.youtube.com'):
            video_id=parse_qs(parsed.query).get('v',[''])[0]
        else:
            raise ValueError('Supply an actual YouTube URL.')
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_id):
            raise ValueError('Invalid YouTube video ID.')
        response=httpx.get('https://www.youtube.com/oembed',params={'url':args.youtube_url,'format':'json'},timeout=30)
        response.raise_for_status()
        video={**response.json(),'url':args.youtube_url,'video_id':video_id}
        replacement='{% youtube '+video_id+' %}\n\nThe [updated narrated walkthrough]('+args.youtube_url+') is a genuine 1920×1080 browser recording, approximately two minutes and twenty-four seconds long.'
        body=re.sub(r'\*\*Updated narrated walkthrough:\*\*[^\n]+',lambda _:replacement,body)
    ready=bool(args.assets_commit and video)
    if ready:
        for target in re.findall(r'\]\(([^)]+)\)',body):
            if '://' not in target and not target.startswith('#'):
                raise ValueError('Unresolved publication link: '+target)
        if 'pending' in body.lower() or 'review notice' in body.lower():
            raise ValueError('Unresolved publication notice.')
    output=ROOT/'docs'/('DEV_SUBMISSION_FINAL.md' if ready else 'DEV_SUBMISSION_REVIEW.md')
    output.write_text(body,encoding='utf-8')
    meta={'title':title,'tags':tags,'existing_article_id':4909609,
          'existing_article_url':'https://dev.to/saif-uk/i-built-a-local-ai-to-turn-a-shops-evening-spreadsheet-hunt-into-a-fix-queue-5b5p',
          'publication_ready':ready,'live_article_updated':False,'assets_commit':args.assets_commit,
          'verified_images':verified_images,'new_video':video,'body_file':output.relative_to(ROOT).as_posix()}
    (ROOT/'docs/DEV_PUBLISHING_META.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    local_body=body
    for item in verified_images:
        local_body=local_body.replace(item['url'],'../'+item['file'])
    if video:
        local_body=local_body.replace('{% youtube '+video['video_id']+' %}',
                                     '<a href="'+html.escape(video['url'],quote=True)+'">Watch the updated narrated walkthrough on YouTube</a>')
    preview_body=markdown.markdown(local_body,extensions=['tables','fenced_code'])
    pending='Ready for the owner’s final review. The live DEV article has not been changed.' if ready else 'Review edition. GitHub asset publication and the new user-supplied YouTube URL are pending. The existing DEV article remains unchanged.'
    template='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>QuietOps — final post review</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f5ee;color:#24392d;font:17px/1.8 system-ui,sans-serif}main{max-width:980px;margin:35px auto;background:white;padding:45px 60px;border:1px solid #dce4d4;border-radius:12px}h1,h2{font-family:Georgia,serif;font-weight:400;line-height:1.25}h1{font-size:38px}h2{font-size:30px;margin-top:40px}p{margin:18px 0}a{color:#366d4b}img,video{display:block;width:100%;height:auto;border:1px solid #dce4d4;border-radius:8px}video{background:#15271f}aside{background:#edf3e4;border-left:4px solid #91a96d;padding:15px 20px;font-size:14px;margin-bottom:30px}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border:1px solid #dce4d4;text-align:left}code{font-size:.9em}pre{overflow:auto}header>p{font-size:13px;color:#62725b}.player{margin:24px 0}@media(max-width:700px){main{margin:0;padding:24px 20px}h1{font-size:30px}table{font-size:11px}td,th{padding:6px}}
</style></head><body><main><aside>STATUS</aside><header><h1>TITLE</h1><p>Tags: TAGS</p></header><div class="player"><video controls preload="metadata" src="../demo/assets/tabpfn/final/video/final_demo.mp4"><track kind="captions" srclang="en" label="English" src="../demo/assets/tabpfn/final/audio/subtitles.vtt"></video></div>BODY</main></body></html>'''
    rendered=template.replace('STATUS',html.escape(pending)).replace('TITLE',html.escape(title)).replace('TAGS',html.escape(', '.join(tags))).replace('BODY',preview_body)
    (ROOT/'docs/DEV_SUBMISSION_TABPFN.html').write_text(rendered,encoding='utf-8')
    print(json.dumps({'ready':ready,'body':str(output),'preview':'docs/DEV_SUBMISSION_TABPFN.html','images':len(verified_images)},indent=2))

if __name__=='__main__':
    main()
