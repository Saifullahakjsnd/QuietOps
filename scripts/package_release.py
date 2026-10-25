"""Create a portable local source/evidence bundle from an explicit allowlist."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE_DIRS=['app','backend','components','lib','scripts','tests','docs']
TOP_FILES=['README.md','LICENSE','.env.example','.gitignore','.gitattributes','.dockerignore','BUILD_PROMPT.md','IMPLEMENTATION_PLAN.md','package.json','package-lock.json','next.config.ts','next-env.d.ts','tsconfig.json','postcss.config.mjs','components.json','playwright.config.ts','compose.yaml','Dockerfile.frontend']

def main():
    output=ROOT/'dist';output.mkdir(exist_ok=True)
    files={ROOT/name for name in TOP_FILES}
    for directory in SOURCE_DIRS:
        files.update(p for p in (ROOT/directory).rglob('*') if p.is_file() and not any(part in {'__pycache__','.pytest_cache','node_modules','.venv','.next'} for part in p.relative_to(ROOT).parts))
    files.update(p for p in (ROOT/'demo').glob('*') if p.is_file())
    for directory in ['fixtures','assets/screenshots']:
        files.update(p for p in (ROOT/'demo'/directory).rglob('*') if p.is_file())
    for name in ['available-voices.json','narration_script.md','narration-scenes.json','narration-timing.json','kokoro_voiceover.wav','subtitles.srt','subtitles.vtt','transcript-qa.json','preview-af_heart.wav','preview-bf_emma.wav','preview-bm_george.wav']:
        p=ROOT/'demo/assets/audio'/name
        if p.exists():files.add(p)
    for name in ['final_demo.mp4','demo_silent.mp4','approved-demo-draft.md','recording-report.json','final-verification.json','playback-verification.json']:
        p=ROOT/'demo/assets/video'/name
        if p.exists():files.add(p)
    for p in (ROOT/'demo/assets/tabpfn').rglob('*'):
        if p.is_file() and not any(part in {'raw','chunks','qa'} for part in p.relative_to(ROOT/'demo/assets/tabpfn').parts) and p.name != 'voiceover-unnormalized.wav':
            files.add(p)
    files={p for p in files if p.is_file()}
    forbidden={'data','logs','node_modules','.venv','.next','.git','dist','__pycache__'}
    for p in files:
        rel=p.relative_to(ROOT)
        if any(part in forbidden for part in rel.parts) or (p.name.startswith('.env') and p.name!='.env.example'):
            raise ValueError(f'Forbidden bundle path: {rel}')
    required=['demo/assets/video/final_demo.mp4','demo/assets/audio/kokoro_voiceover.wav','demo/assets/audio/subtitles.srt','docs/DEV_SUBMISSION.md']
    if not all(ROOT/name in files for name in required):raise ValueError('A required final asset is missing.')
    manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    destination=output/'quietops-local-bundle.zip'
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for p in sorted(files):archive.write(p,str(p.relative_to(ROOT)))
        archive.writestr('BUNDLE_MANIFEST.json',json.dumps({'scope':'Local source/evidence handoff; no private working data or model weights','files':manifest},indent=2))
    with zipfile.ZipFile(destination) as archive:
        bad=archive.testzip()
        if bad:raise ValueError(f'Corrupt archive member: {bad}')
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {destination.name}\n',encoding='utf-8')
    print(json.dumps({'archive':str(destination),'files':len(files),'bytes':destination.stat().st_size,'sha256':digest,'archive_integrity':'passed'},indent=2))

if __name__=='__main__':main()
