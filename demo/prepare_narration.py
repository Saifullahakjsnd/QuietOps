"""Prepare real Kokoro assets, inspect voices, or synthesize ONLY an explicitly supplied voice."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT/'data'/'kokoro'
ASSETS = ROOT/'demo'/'assets'/'audio'
BASE = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--voice',help='User-selected voice; omitted means inspect only, no final narration.')
    parser.add_argument('--preview',action='store_true',help='Generate labelled comparison previews, never a final voice choice.')
    args=parser.parse_args()
    MODEL_DIR.mkdir(parents=True,exist_ok=True); ASSETS.mkdir(parents=True,exist_ok=True)
    for filename in ['kokoro-v1.0.onnx','voices-v1.0.bin']:
        destination=MODEL_DIR/filename
        if not destination.exists():
            print(f'Downloading genuine Kokoro asset: {filename}',flush=True)
            temporary=destination.with_suffix(destination.suffix+'.partial')
            urllib.request.urlretrieve(BASE+filename,temporary)
            temporary.replace(destination)
    from kokoro_onnx import Kokoro
    import soundfile as sf
    import numpy as np
    kokoro=Kokoro(str(MODEL_DIR/'kokoro-v1.0.onnx'),str(MODEL_DIR/'voices-v1.0.bin'))
    voices=sorted(kokoro.get_voices())
    english=[voice for voice in voices if voice.startswith(('af_','am_','bf_','bm_'))]
    report={'engine':'kokoro-onnx','model':'Kokoro-82M v1.0','source':BASE,'voices':voices,'english_voices':english,
            'files':{name:hashlib.sha256((MODEL_DIR/name).read_bytes()).hexdigest() for name in ['kokoro-v1.0.onnx','voices-v1.0.bin']},'final_voice_selected':args.voice}
    (ASSETS/'available-voices.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
    if args.preview:
        for voice in ['af_heart','bf_emma','bm_george']:
            if voice not in english: continue
            samples,rate=kokoro.create('This is QuietOps. Catch the small things. Keep the decision. Get a little breathing room.',voice=voice,speed=1.0,lang='en-gb' if voice.startswith('b') else 'en-us')
            sf.write(ASSETS/f'preview-{voice}.wav',samples,rate)
            print(f'Preview saved: {voice}',flush=True)
    if args.voice:
        if args.voice not in english: raise ValueError('Choose a supported English voice from the inspected configuration.')
        text=(ASSETS/'narration_script.md').read_text(encoding='utf-8')
        paragraphs=[p.strip() for p in text.split('\n\n') if p.strip() and not p.lstrip().startswith('#')]
        audio=[]; chunks=[]; elapsed=0.0
        for paragraph in paragraphs:
            samples,rate=kokoro.create(paragraph,voice=args.voice,speed=1.05,lang='en-gb' if args.voice.startswith('b') else 'en-us')
            duration=len(samples)/rate
            chunks.append({'start':elapsed,'end':elapsed+duration,'text':paragraph})
            audio.append(samples); audio.append(np.zeros(int(rate*.35),dtype=np.float32));elapsed+=duration+.35
        sf.write(ASSETS/'kokoro_voiceover.wav',np.concatenate(audio),rate)
        (ASSETS/'narration-timing.json').write_text(json.dumps({'voice':args.voice,'sample_rate':rate,'duration':elapsed,'chunks':chunks},indent=2),encoding='utf-8')

if __name__=='__main__': main()
