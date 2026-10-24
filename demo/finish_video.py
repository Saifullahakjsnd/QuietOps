"""Genuine user-selected Kokoro narration, scene-aligned captions and final MP4."""
import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
import textwrap
import time
from pathlib import Path
import numpy as np
import onnxruntime as rt
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT/'demo/assets/audio'
VIDEO = ROOT/'demo/assets/video'
RATE = 24000

def run(arguments):
    result=subprocess.run(arguments,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode:raise RuntimeError(result.stderr[-5000:])
    return result

def stamp(seconds):
    ms=round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def subtitle_groups(text):
    result=[]
    for sentence in re.split(r'(?<=[.!?])\s+',text.strip()):
        group=[]
        for word in sentence.split():
            if len(' '.join(group+[word]))>88 and group:
                result.append(' '.join(group));group=[]
            group.append(word)
        if group:result.append(' '.join(group))
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--voice',required=True,help='Explicit user-selected voice. George is bm_george.')
    args=parser.parse_args()
    plan=json.loads((AUDIO/'narration-scenes.json').read_text(encoding='utf-8'))
    if args.voice!=plan['voice']:raise ValueError('Scene plan must name the user-selected voice.')
    if plan.get('video_sha256')!=hashlib.sha256((VIDEO/'demo_silent.mp4').read_bytes()).hexdigest():
        raise ValueError('Source recording changed. Inspect its actual scenes and update narration-scenes.json before aligning narration.')
    text=(AUDIO/'narration_script.md').read_text(encoding='utf-8')
    paragraphs=[p.strip() for p in text.split('\n\n') if p.strip() and not p.lstrip().startswith('#')]
    if len(paragraphs)!=len(plan['scenes']):raise ValueError('One paragraph is required per scene.')
    model=ROOT/'data/kokoro/kokoro-v1.0.onnx';voices=ROOT/'data/kokoro/voices-v1.0.bin'
    opts=rt.SessionOptions();opts.intra_op_num_threads=2;opts.inter_op_num_threads=1
    opts.execution_mode=rt.ExecutionMode.ORT_SEQUENTIAL
    session=rt.InferenceSession(str(model),sess_options=opts,providers=['CPUExecutionProvider'])
    kokoro=Kokoro.from_session(session,str(voices))
    if args.voice not in kokoro.get_voices():raise ValueError('Selected voice absent from installed voice pack.')
    chunk_dir=AUDIO/'chunks';chunk_dir.mkdir(exist_ok=True)
    master=np.zeros(round(plan['duration']*RATE),dtype=np.float32)
    cues=[];report=[];started=time.perf_counter()
    for scene,paragraph in zip(plan['scenes'],paragraphs):
        print(f"Synthesizing {scene['id']} with {args.voice}",flush=True)
        raw,rate=kokoro.create(paragraph,voice=args.voice,speed=1.0,lang='en-gb')
        if rate!=RATE:raise ValueError('Unexpected model sample rate.')
        raw_path=chunk_dir/f"{scene['id']}-raw.wav";sf.write(raw_path,raw,rate,subtype='PCM_16')
        window=scene['end']-scene['start'];raw_duration=len(raw)/rate
        tempo=max(1.0,raw_duration/(window-.10))
        if tempo>1.30:raise ValueError(f"Rewrite {scene['id']}: {raw_duration:.2f}s does not fit {window:.2f}s naturally.")
        ready=chunk_dir/f"{scene['id']}.wav"
        run(['ffmpeg','-y','-v','error','-i',str(raw_path),'-af',f'atempo={tempo:.8f},afade=t=in:st=0:d=0.012','-ar',str(RATE),'-ac','1',str(ready)])
        speech,_=sf.read(ready,dtype='float32');duration=len(speech)/RATE
        start=scene['start']+min(.20,max(0,(window-duration)/2));end=start+duration
        if end>scene['end']+.03:raise ValueError('Speech crosses scene boundary.')
        offset=round(start*RATE);master[offset:offset+len(speech)]=speech
        groups=subtitle_groups(paragraph);weights=[len(group.split()) for group in groups];total=sum(weights);cursor=start
        for group,weight in zip(groups,weights):
            cue_end=cursor+duration*weight/total
            cues.append({'start':cursor,'end':cue_end,'text':group,'scene':scene['id']});cursor=cue_end
        report.append({**scene,'text':paragraph,'speech_start':round(start,3),'speech_end':round(end,3),'raw_duration':round(raw_duration,3),'tempo':round(tempo,4)})
    peak=float(np.max(np.abs(master)))
    if peak==0 or not np.isfinite(master).all():raise ValueError('Generated master empty or invalid.')
    if peak>.95:master*=.95/peak
    unnormalized=AUDIO/'voiceover-unnormalized.wav';sf.write(unnormalized,master,RATE,subtype='PCM_16')
    output_audio=AUDIO/'kokoro_voiceover.wav'
    run(['ffmpeg','-y','-v','error','-i',str(unnormalized),'-af','loudnorm=I=-16:TP=-1.5:LRA=9','-ar',str(RATE),'-ac','1',str(output_audio)])
    srt=AUDIO/'subtitles.srt'
    srt.write_text('\n\n'.join(f"{i}\n{stamp(c['start'])} --> {stamp(c['end'])}\n"+'\n'.join(textwrap.wrap(c['text'],width=46,break_long_words=False)) for i,c in enumerate(cues,1))+'\n',encoding='utf-8')
    # Entire source UI is retained above an 81px caption strip; no controls hidden.
    # SRT's default ASS canvas is 384x288, so size 9 becomes about 34px
    # at 1080p. Two caption lines fit fully inside the reserved 81px strip.
    vf="scale=1776:999,pad=1920:1080:72:0:color=0x15271f,subtitles=demo/assets/audio/subtitles.srt:force_style='FontName=Arial,FontSize=9,PrimaryColour=&H00FFFFFF,OutlineColour=&H0015271F,BorderStyle=1,Outline=0.6,Shadow=0,Alignment=2,MarginV=2'"
    final=VIDEO/'final_demo.mp4'
    run(['ffmpeg','-y','-v','error','-threads','2','-i',str(VIDEO/'demo_silent.mp4'),'-i',str(output_audio),
         '-filter_threads','2','-vf',vf,'-map','0:v:0','-map','1:a:0',
         '-c:v','libx264','-threads','2','-preset','medium','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
         '-metadata:s:a:0','language=eng',
         '-metadata','title=QuietOps — Evidence, a draft, and a quieter evening',
         '-metadata','comment=Fictional shop data; real local Ministral inference; genuine Kokoro-82M bm_george narration.',
         '-movflags','+faststart','-t',str(plan['duration']),str(final)])
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)]).stdout)
    run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'])
    info=sf.info(output_audio)
    verification={'voice':args.voice,'user_selection':'George (bm_george), explicitly selected in chat',
                  'engine':'kokoro-onnx','engine_version':importlib.metadata.version('kokoro-onnx'),
                  'model':'Kokoro-82M v1.0','model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
                  'voices_sha256':hashlib.sha256(voices.read_bytes()).hexdigest(),
                  'duration_seconds':plan['duration'],'audio_sample_rate':info.samplerate,'audio_frames':info.frames,
                  'subtitle_cues':len(cues),'subtitle_alignment':'Scene-anchored phrases, duration proportional to word count; not forced word alignment.',
                  'source_screen_timing_preserved':True,'full_decode_passed':True,'scenes':report,'subtitle_cue_timings':cues,
                  'probe':probe,'elapsed_seconds':round(time.perf_counter()-started,2),
                  'outputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [output_audio,srt,final]}}
    (AUDIO/'narration-timing.json').write_text(json.dumps({'voice':args.voice,'sample_rate':RATE,'duration':plan['duration'],'chunks':report},indent=2),encoding='utf-8')
    (VIDEO/'final-verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    manifest=json.loads((AUDIO/'available-voices.json').read_text(encoding='utf-8'));manifest['final_voice_selected']=args.voice
    (AUDIO/'available-voices.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({k:verification[k] for k in ['voice','duration_seconds','subtitle_cues','full_decode_passed','elapsed_seconds','outputs']},indent=2),flush=True)

if __name__=='__main__':main()
