import { chromium, expect } from '@playwright/test';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

async function main(){
 const root=process.cwd();const qa=path.join(root,'demo/assets/video/qa');
 await mkdir(qa,{recursive:true});
 await writeFile(path.join(qa,'player.html'),'<!doctype html><html lang="en"><meta charset="utf-8"><title>QuietOps video QA</title><style>html,body{margin:0;background:#15271f;height:100%;overflow:hidden}video{display:block;width:100%;height:100%;object-fit:contain}</style><video controls preload="auto" src="../final_demo.mp4"></video></html>');
 const browser=await chromium.launch({channel:'msedge',headless:true,args:['--autoplay-policy=no-user-gesture-required']});
 try {
 const page=await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1});
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(qa,'player.html')).href);
 await page.waitForFunction(()=>{const v=document.querySelector('video');return v && v.readyState>=2;});
 const metadata=await page.evaluate(()=>{const v=document.querySelector('video')!;return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,readyState:v.readyState,error:v.error?.message ?? null};});
 expect(metadata.width).toBe(1920);expect(metadata.height).toBe(1080);expect(Math.abs(metadata.duration-118.12)).toBeLessThan(.15);expect(metadata.error).toBeNull();
 await page.evaluate(async()=>{const v=document.querySelector('video')!;await v.play();});
 await page.waitForFunction(()=>document.querySelector('video')!.currentTime>1,{},{timeout:15000});
 const playing=await page.evaluate(()=>{const v=document.querySelector('video')!;return {currentTime:v.currentTime,paused:v.paused,decodedFrames:v.getVideoPlaybackQuality().totalVideoFrames};});
 expect(playing.paused).toBe(false);expect(playing.currentTime).toBeGreaterThan(.5);expect(playing.decodedFrames).toBeGreaterThan(0);
 for(const [name,at] of [['evidence',43],['local-ai',61],['review',80],['approved',89]] as const){
   await page.evaluate(async(time)=>{const v=document.querySelector('video')!;v.pause();v.controls=false;await new Promise<void>(resolve=>{v.addEventListener('seeked',()=>resolve(),{once:true});v.currentTime=time;});},at);
   await page.locator('video').screenshot({path:path.join(qa,`final-${name}.png`)});
 }
 await page.goto(pathToFileURL(path.join(root,'docs/DEV_SUBMISSION.html')).href);
 await expect(page.getByRole('heading',{name:'What I Built',exact:true})).toBeVisible();
 const article=await page.evaluate(()=>({images:[...document.images].map(image=>({source:image.getAttribute('src'),loaded:image.complete&&image.naturalWidth>0})),headings:[...document.querySelectorAll('h2')].map(h=>h.textContent),width:document.documentElement.scrollWidth}));
 expect(article.images.length).toBeGreaterThanOrEqual(4);expect(article.images.every(image=>image.loaded)).toBe(true);
 await page.screenshot({path:path.join(qa,'article-preview.png'),fullPage:true});
 expect(errors).toEqual([]);
 const report={verified_at:new Date().toISOString(),browser:'Microsoft Edge / Playwright',metadata,playing,article,browser_errors:errors};
 await writeFile(path.join(root,'demo/assets/video/playback-verification.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
 } finally { await browser.close(); }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
