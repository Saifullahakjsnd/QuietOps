import { chromium, expect } from '@playwright/test';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

async function main(){
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
   const page=await browser.newPage({viewport:{width:1440,height:1200},deviceScaleFactor:1});
   await page.goto(pathToFileURL(path.resolve('docs/POST_PREVIEW.html')).href);
   await expect(page.getByRole('heading',{level:1})).toBeVisible();
   await expect(page.getByRole('heading',{name:'What I Built',exact:true})).toBeVisible();
   await page.screenshot({path:'demo/assets/screenshots/08-post-preview.png'});
   console.log('Captured the actual local article rendering for the GitHub README.');
 } finally{await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
