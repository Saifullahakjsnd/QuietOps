import { chromium, expect } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

async function main() {
 const base = process.env.QUIETOPS_URL || 'http://127.0.0.1:3002';
 const assetRoot = path.resolve('demo/assets');
 await mkdir(path.join(assetRoot,'screenshots'),{recursive:true});
 await mkdir(path.join(assetRoot,'video'),{recursive:true});
 const browser = await chromium.launch({channel:'msedge',headless:true});
 const context = await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,
   recordVideo:{dir:path.join(assetRoot,'video/raw'),size:{width:1920,height:1080}},reducedMotion:'reduce'});
 const page = await context.newPage();
 const video = page.video();
 const errors:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));
 const started = Date.now();
 const pause = (ms:number)=>page.waitForTimeout(ms);
 try {
   await page.goto(base);await expect(page.getByRole('heading',{name:'Your shop, a little quieter.'})).toBeVisible();
   await expect(page.getByText('Opening your local workspace…',{exact:true})).toBeHidden();
   const startDemo = page.getByRole('button',{name:'Explore a demo shop'});
   if(!await startDemo.isVisible()) throw new Error('Use an empty, isolated QUIETOPS_DATA workspace for a reproducible recording.');
   console.log('Recording: empty workspace and fictional demo selection.');
   await pause(7000);await startDemo.click();
   await expect(page.getByText('Fictional shop demo',{exact:true})).toBeVisible();await pause(8500);
   await page.screenshot({path:path.join(assetRoot,'screenshots/01-dashboard.png'),fullPage:true});
   await page.getByRole('button',{name:'Import & mapping',exact:true}).click();await pause(6500);
   await page.screenshot({path:path.join(assetRoot,'screenshots/06-imports.png'),fullPage:true});
   await page.getByRole('button',{name:'Inventory',exact:true}).click();await pause(8500);
   await page.screenshot({path:path.join(assetRoot,'screenshots/07-inventory.png'),fullPage:true});
   await page.getByRole('button',{name:'Issue inbox',exact:true}).click();await pause(4000);
   await page.getByRole('button',{name:/Oat milk needs a stock check/}).first().click();
   await expect(page.getByText('THE CALCULATION',{exact:true})).toBeVisible();await pause(9000);
   await page.screenshot({path:path.join(assetRoot,'screenshots/02-evidence.png')});
   await page.getByText('Assumptions & limits',{exact:true}).click();await pause(6000);
   const explain = page.getByRole('button',{name:'Explain with local AI'});
   await explain.scrollIntoViewIfNeeded();await expect(explain).toBeEnabled({timeout:180000});
   console.log('Recording: invoking real Ministral model.');
   await explain.click();await expect(page.getByText('Suggested next step',{exact:true})).toBeVisible({timeout:210000});
   await page.locator('.ai-section').scrollIntoViewIfNeeded();await pause(12000);
   await page.screenshot({path:path.join(assetRoot,'screenshots/03-local-ai.png')});
   await page.getByRole('button',{name:'Create action draft'}).click();
   await expect(page.getByRole('heading',{name:'Fix queue',exact:true})).toBeVisible();await pause(6000);
   await page.getByRole('button',{name:'Review & decide'}).first().click();await pause(9500);
   await page.getByRole('button',{name:'Approve for export',exact:true}).click();
   await expect(page.getByText('approved',{exact:true}).first()).toBeVisible();await pause(5000);
   await page.screenshot({path:path.join(assetRoot,'screenshots/04-approved.png'),fullPage:true});
   const downloadPromise = page.waitForEvent('download');
   await page.getByRole('link',{name:'Export approved drafts'}).click();
   const download = await downloadPromise;await download.saveAs(path.join(assetRoot,'video/approved-demo-draft.md'));await pause(4500);
   await page.getByRole('button',{name:'Audit history',exact:true}).click();await pause(7000);
   await page.getByRole('button',{name:'Overview',exact:true}).click();await pause(8500);
   if(errors.length) throw new Error(errors.join('\n'));
 } finally { await context.close();await browser.close(); }
 const raw = await video!.path();
 const output = path.join(assetRoot,'video/demo_silent.mp4');
 const convert = spawnSync('ffmpeg',['-y','-i',raw,'-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',output],{encoding:'utf8'});
 if(convert.status!==0) throw new Error(convert.stderr);
 const probe = spawnSync('ffprobe',['-v','error','-show_entries','format=duration:stream=width,height,codec_name','-of','json',output],{encoding:'utf8'});
 if(probe.status!==0) throw new Error(probe.stderr);
 const report = {recorded_at:new Date().toISOString(),elapsed_ms:Date.now()-started,synthetic:true,real_local_inference:true,output,probe:JSON.parse(probe.stdout),browser_errors:errors};
 await writeFile(path.join(assetRoot,'video/recording-report.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report,null,2));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
