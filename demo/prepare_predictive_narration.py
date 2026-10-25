"""Measure the already user-selected George narration to pace a fresh real recording."""
import json
from pathlib import Path
import numpy as np
import onnxruntime as rt
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'demo/assets/tabpfn/final/audio'

def main():
    plan = json.loads((AUDIO / 'scene-text.json').read_text(encoding='utf-8'))
    if plan['voice'] != 'bm_george':
        raise ValueError('This edition retains the previously user-selected George voice.')
    options = rt.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = rt.InferenceSession(str(ROOT/'data/kokoro/kokoro-v1.0.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
    kokoro = Kokoro.from_session(session, str(ROOT/'data/kokoro/voices-v1.0.bin'))
    assert plan['voice'] in kokoro.get_voices()
    chunks = AUDIO / 'chunks'
    chunks.mkdir(exist_ok=True)
    for scene in plan['scenes']:
        audio, rate = kokoro.create(scene['text'], voice=plan['voice'], speed=1, lang='en-gb')
        assert rate == 24000 and np.isfinite(audio).all()
        sf.write(chunks / (scene['id']+'-preview.wav'), audio, rate)
        scene['speech_seconds'] = round(len(audio)/rate, 3)
        scene['minimum_window_seconds'] = round(len(audio)/rate/1.12+.7, 3)
        print(scene['id'], scene['speech_seconds'], flush=True)
    (AUDIO/'scene-text.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
    print('Minimum scene duration:', sum(s['minimum_window_seconds'] for s in plan['scenes']), flush=True)

if __name__ == '__main__':
    main()
