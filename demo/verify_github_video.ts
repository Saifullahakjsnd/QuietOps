import {chromium,expect} from '@playwright/test';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';

async function main(){
 const meta=JSON.parse(await readFile('docs/DEV_PUBLISHING_META.json','utf8'));
 if(meta.new_video?.hosting!=='github')throw new Error('Prepare the verified GitHub video edition first.');
 const behavior=await readFile('data/forem-gifVideo.js','utf8');
 const browser=await chromium.launch({channel:'msedge',headless:true});const errors:string[]=[];
 const qa=path.resolve('demo/assets/tabpfn/final/qa');await mkdir(qa,{recursive:true});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
  await page.setContent(`<video controls preload="metadata" width="1200"><source src="${meta.new_video.url}" type="video/mp4"></video>`);
  await page.waitForFunction(()=>document.querySelector('video')!.readyState>=2,{},{timeout:45000});
  await page.evaluate(()=>document.querySelector('video')!.play());await page.waitForFunction(()=>document.querySelector('video')!.currentTime>1,{},{timeout:30000});
  const full=await page.evaluate(()=>{const v=document.querySelector('video')!;return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,controls:v.controls,muted:v.muted,currentTime:v.currentTime,error:v.error?.message??null};});
  expect(full.duration).toBe(143.76);expect(full.controls).toBe(true);expect(full.muted).toBe(false);expect(full.error).toBeNull();
  await page.setContent(`<h1>DEV-style inline preview</h1><video data-gif-video="true" autoplay loop muted playsinline controls width="1200" preload="metadata"><source src="${meta.new_video.preview_url}" type="video/mp4"></video><p><a href="${meta.new_video.url}">Watch or download the full narrated demo</a></p>`);
  await page.addScriptTag({content:behavior.replace(/^export /,'')+'\ninitializeGifVideos();'});
  await page.waitForFunction(()=>document.querySelector('video')!.currentTime>1,{},{timeout:45000});
  const preview=await page.evaluate(()=>{const v=document.querySelector('video')!;return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,controls:v.controls,muted:v.muted,loop:v.loop,currentTime:v.currentTime,error:v.error?.message??null};});
  expect(preview.controls).toBe(false);expect(preview.muted).toBe(true);expect(preview.loop).toBe(true);expect(preview.error).toBeNull();
  await page.screenshot({path:path.join(qa,'github-inline-preview.png')});expect(errors).toEqual([]);
  const report={verified_at:new Date().toISOString(),full,preview,public_video_url:meta.new_video.url,public_preview_url:meta.new_video.preview_url,
   forems_behavior_source:'https://github.com/forem/forem/blob/main/app/javascript/utilities/gifVideo.js',
   scope:'Public GitHub playback verified in Microsoft Edge with the current upstream Forem GIF-video behavior applied locally; this is not a live DEV post publication.',browser_errors:errors};
  await writeFile('demo/assets/tabpfn/final/video/github-playback-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1;});
