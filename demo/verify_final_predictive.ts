import { chromium, expect } from '@playwright/test';
import { readFile,writeFile,mkdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

async function main(){
 const root=path.resolve('demo/assets/tabpfn/final'), qa=path.join(root,'qa');await mkdir(qa,{recursive:true});
 const plan=JSON.parse(await readFile(path.join(root,'audio/narration-scenes.json'),'utf8'));
 await writeFile(path.join(qa,'player.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><title>QuietOps final video review</title><style>html,body{margin:0;background:#15271f;height:100%;overflow:hidden}video{display:block;width:100%;height:100%;object-fit:contain}</style><video controls preload="auto" src="../video/final_demo.mp4"></video></html>');
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--autoplay-policy=no-user-gesture-required']});const errors:string[]=[];
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(qa,'player.html')).href);
  await page.waitForFunction(()=>document.querySelector('video')!.readyState>=2);
  const metadata=await page.evaluate(()=>{const v=document.querySelector('video')!;return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,error:v.error?.message??null};});
  expect(metadata.width).toBe(1920);expect(metadata.height).toBe(1080);expect(Math.abs(metadata.duration-plan.duration)).toBeLessThan(.1);expect(metadata.error).toBeNull();
  await page.evaluate(()=>document.querySelector('video')!.play());await page.waitForFunction(()=>document.querySelector('video')!.currentTime>1);
  const playing=await page.evaluate(()=>{const v=document.querySelector('video')!;return {currentTime:v.currentTime,paused:v.paused,decodedFrames:v.getVideoPlaybackQuality().totalVideoFrames};});expect(playing.paused).toBe(false);expect(playing.decodedFrames).toBeGreaterThan(0);
  for(const id of ['05-disagreement','06-evaluation','08-ministral','09-edit','10-approve']){
   const s=plan.scenes.find((x:any)=>x.id===id),at=s.start+(s.end-s.start)*.6;
   await page.evaluate(async time=>{const v=document.querySelector('video')!;v.pause();v.controls=false;await new Promise<void>(resolve=>{v.addEventListener('seeked',()=>resolve(),{once:true});v.currentTime=time;});},at);
   await page.locator('video').screenshot({path:path.join(qa,id+'.png')});
  }
  await page.goto(pathToFileURL(path.resolve('docs/DEV_SUBMISSION_TABPFN.html')).href);
  await expect(page.getByRole('heading',{name:'What I Built',exact:true})).toBeVisible();
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
  const article=await page.evaluate(()=>({images:[...document.images].map(i=>({source:i.getAttribute('src'),loaded:i.complete&&i.naturalWidth>0})),headings:[...document.querySelectorAll('h2')].map(h=>h.textContent)}));
  expect(article.images.length).toBeGreaterThanOrEqual(4);expect(article.images.every(i=>i.loaded)).toBe(true);
  expect(article.headings).toEqual(['What I Built','Demo','Code','How I Built It','Why Does Open Innovation Matter?','The Lazy Payoff','Prize Categories']);
  await page.screenshot({path:path.join(qa,'article-preview.png'),fullPage:true});
  expect(errors).toEqual([]);
  const report={verified_at:new Date().toISOString(),browser:'Microsoft Edge / Playwright',metadata,playing,article,browser_errors:errors};
  await writeFile(path.join(root,'video/playback-verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
