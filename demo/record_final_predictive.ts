import { chromium, expect } from '@playwright/test';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { createHash } from 'node:crypto';

async function main(){
 const root=path.resolve('demo/assets/tabpfn/final'), base=process.env.QUIETOPS_URL||'http://127.0.0.1:3002';
 const script=JSON.parse(await readFile(path.join(root,'audio/scene-text.json'),'utf8'));
 await mkdir(path.join(root,'video/raw'),{recursive:true});await mkdir(path.join(root,'screenshots'),{recursive:true});
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,reducedMotion:'reduce',recordVideo:{dir:path.join(root,'video/raw'),size:{width:1920,height:1080}}});
 const page=await context.newPage(), video=page.video();const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 const scenes:any[]=[];let state:any;const began=Date.now();
 const pause=(ms:number)=>page.waitForTimeout(ms);
 async function scene(id:string,work:()=>Promise<void>,shot?:string){
  const entry=script.scenes.find((s:any)=>s.id===id);if(!entry?.minimum_window_seconds)throw new Error('Measure narration before recording.');
  const start=(Date.now()-began)/1000;console.log('Recording '+id);await work();
  await pause(Math.max(0,entry.minimum_window_seconds*1000-(Date.now()-began-start*1000)));
  if(shot)await page.screenshot({path:path.join(root,'screenshots',shot)});
  scenes.push({id,start,end:(Date.now()-began)/1000,screen:entry.text});
 }
 try{
  await page.goto(base);await expect(page.getByText('Opening your local workspace…',{exact:true})).toBeHidden();
  const demo=page.getByRole('button',{name:'Explore a demo shop'});if(!await demo.isVisible())throw new Error('Use an empty isolated data directory.');
  await scene('01-evening',async()=>{});
  await scene('02-deterministic',async()=>{await demo.click();await expect(page.getByText('Fictional shop demo',{exact:true})).toBeVisible();},'01-original-dashboard.png');
  await scene('03-history',async()=>{
   await page.getByRole('button',{name:'Looking Ahead',exact:true}).click();await pause(1500);
   await page.getByRole('button',{name:'Load predictive example',exact:true}).click();
   await expect(page.getByRole('button',{name:'Run TabPFN prediction',exact:true})).toBeEnabled();
  },'02-predictive-history.png');
  await scene('04-predict',async()=>{
   await page.getByRole('button',{name:'Run TabPFN prediction',exact:true}).click();
   await expect(page.getByRole('heading',{name:'A closer look at the shelf',exact:true})).toBeVisible({timeout:180000});
  });
  await scene('05-disagreement',async()=>{
   await page.getByRole('heading',{name:'A closer look at the shelf',exact:true}).evaluate(e=>e.scrollIntoView({block:'start'}));
   await expect(page.getByRole('row').filter({hasText:'SKU-007'})).toContainText('Beyond cover rule');
  },'03-predictive-risk.png');
  await scene('06-evaluation',async()=>{
   await page.getByRole('heading',{name:'Held-out historical comparison',exact:true}).evaluate(e=>e.scrollIntoView({block:'start'}));
  },'04-evaluation.png');
  await scene('07-evidence',async()=>{
   await page.getByRole('row').filter({hasText:'SKU-007'}).getByRole('button',{name:'Inspect prediction'}).click();
   await expect(page.getByText('THE CALCULATION',{exact:true})).toBeVisible();
  },'05-evidence.png');
  await scene('08-ministral',async()=>{
   const explain=page.getByRole('button',{name:'Explain with local AI',exact:true});await explain.scrollIntoViewIfNeeded();await expect(explain).toBeEnabled();
   const response=page.waitForResponse(r=>r.url().endsWith('/explain')&&r.request().method()==='POST',{timeout:210000});
   await explain.click();const result=await response;if(!result.ok())throw new Error(await result.text());
   await expect(page.getByText('Suggested next step',{exact:true})).toBeVisible();await page.locator('.ai-section').scrollIntoViewIfNeeded();
  },'06-ministral.png');
  await scene('09-edit',async()=>{
   await page.getByRole('button',{name:'Create action draft',exact:true}).click();
   await page.getByRole('button',{name:'Review & decide',exact:true}).first().click();
   const text=page.getByLabel('Draft text',{exact:true});await text.fill((await text.inputValue())+'\n\nReviewer edit (fictional demo): Please confirm the delivery plan and current stock before considering a purchase.');
  },'07-editable-draft.png');
  await scene('10-approve',async()=>{
   await page.getByRole('button',{name:'Approve for export',exact:true}).click();
   const download=page.waitForEvent('download');await page.getByRole('link',{name:'Export approved drafts'}).click();
   await (await download).saveAs(path.join(root,'video/approved-supplier-review.md'));
  },'08-approved.png');
  await scene('11-close',async()=>{
   await page.getByRole('button',{name:'Looking Ahead',exact:true}).click();
   await page.getByRole('heading',{name:'Held-out historical comparison',exact:true}).evaluate(e=>e.scrollIntoView({block:'start'}));
  },'09-result-and-limits.png');
  state=await (await context.request.get(base+'/api/state')).json();
  expect(state.prediction_run.model.inference_ran).toBe(true);expect(state.predictions.find((p:any)=>p.subject==='SKU-007').ai.model).toContain('ministral');expect(errors).toEqual([]);
 }finally{await context.close();await browser.close();}
 const source=await video!.path(), destination=path.join(root,'video/demo_silent.mp4');
 const converted=spawnSync('ffmpeg',['-y','-v','error','-i',source,'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',destination],{encoding:'utf8'});if(converted.status!==0)throw new Error(converted.stderr);
 const probe=JSON.parse(spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','json',destination],{encoding:'utf8'}).stdout);
 const plan={voice:script.voice,video:'demo/assets/tabpfn/final/video/demo_silent.mp4',video_sha256:createHash('sha256').update(await readFile(destination)).digest('hex'),duration:Number(probe.format.duration),timing_source:'Actual browser scene timestamps, paced to measured Kokoro speech. No model latency claim is inferred from scene length.',scenes};
 await writeFile(path.join(root,'audio/narration-scenes.json'),JSON.stringify(plan,null,2));
 await writeFile(path.join(root,'video/recording-report.json'),JSON.stringify({recorded_at:new Date().toISOString(),synthetic:true,constructed_example_selected_after_exploration:true,model:state.prediction_run.model,comparison:state.prediction_run.comparison,local_explanation:state.predictions.find((p:any)=>p.subject==='SKU-007').ai,browser_errors:errors,scenes,duration_seconds:plan.duration,source:source},null,2));
 console.log(JSON.stringify({duration:plan.duration,scenes:scenes.length,video:destination}));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
