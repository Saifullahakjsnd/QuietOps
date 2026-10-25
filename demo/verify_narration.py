"""Independent, CPU-only ASR spot check of the generated narration.

Transcription is evidence for speech continuity and rough text matching, not a
claim of perfect pronunciation or human listening review. FFmpeg supplies PCM
directly to avoid PyAV version-specific file-decoder APIs.
"""
import difflib
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
import numpy as np
from faster_whisper import WhisperModel

ROOT=Path(__file__).resolve().parents[1]
AUDIO=ROOT/'demo/assets/audio'

def tokens(text):
    return re.findall(r"[a-z]+|\d+",text.lower())

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--audio-dir',default='demo/assets/audio')
    args=parser.parse_args()
    global AUDIO
    AUDIO=(ROOT/args.audio_dir).resolve()
    audio_hash=hashlib.sha256((AUDIO/'kokoro_voiceover.wav').read_bytes()).hexdigest()
    model=WhisperModel('tiny.en',device='cpu',compute_type='int8',cpu_threads=2,num_workers=1,download_root=str(ROOT/'data/whisper-qa'))
    result=subprocess.run(['ffmpeg','-v','error','-i',str(AUDIO/'kokoro_voiceover.wav'),'-ar','16000','-ac','1','-f','f32le','-'],capture_output=True,check=True)
    samples=np.frombuffer(result.stdout,dtype=np.float32).copy()
    segments,info=model.transcribe(samples,beam_size=5,word_timestamps=True,language='en',vad_filter=False)
    items=[]
    for segment in segments:
        item={'start':segment.start,'end':segment.end,'text':segment.text,
              'words':[{'word':word.word,'start':word.start,'end':word.end,'probability':word.probability} for word in (segment.words or [])]}
        items.append(item)
        print(f'{segment.start:.2f}--{segment.end:.2f} {segment.text}',flush=True)
    expected=' '.join(p for p in (AUDIO/'narration_script.md').read_text(encoding='utf-8').split('\n\n') if p.strip() and not p.lstrip().startswith('#'))
    observed=' '.join(item['text'] for item in items)
    similarity=difflib.SequenceMatcher(None,tokens(expected),tokens(observed),autojunk=False).ratio()
    if audio_hash!=hashlib.sha256((AUDIO/'kokoro_voiceover.wav').read_bytes()).hexdigest():raise ValueError('Narration changed during QA; rerun on the completed master.')
    report={'model':'Systran/faster-whisper-tiny.en','device':'cpu','language':info.language,'duration':info.duration,'audio_sha256':audio_hash,
            'purpose':'Independent speech-continuity and rough content check; ASR can itself make recognition errors.',
            'token_sequence_similarity':similarity,'expected_word_tokens':len(tokens(expected)),'observed_word_tokens':len(tokens(observed)),
            'segments':items}
    (AUDIO/'transcript-qa.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'Token sequence similarity: {similarity:.3f}',flush=True)

if __name__=='__main__':main()
