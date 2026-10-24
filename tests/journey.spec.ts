import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

test('real demo, evidence, local inference, review and approved export', async({page,request})=>{
  const errors:string[]=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Your shop, a little quieter.'})).toBeVisible();
  await expect(page.getByText('Opening your local workspace…',{exact:true})).toBeHidden();
  if(await page.getByRole('button',{name:'Explore a demo shop'}).isVisible()) await page.getByRole('button',{name:'Explore a demo shop'}).click();
  await expect(page.getByText('Fictional shop demo',{exact:true})).toBeVisible();
  await mkdir('demo/assets/screenshots',{recursive:true});
  await page.screenshot({path:'demo/assets/screenshots/01-dashboard.png',fullPage:true});
  await page.getByRole('button',{name:/Oat milk needs a stock check/}).first().click();
  await expect(page.getByText('THE CALCULATION',{exact:true})).toBeVisible();
  await expect(page.getByText('inventory.csv',{exact:true}).first()).toBeVisible();
  await page.screenshot({path:'demo/assets/screenshots/02-evidence.png'});
  const explain=page.getByRole('button',{name:'Explain with local AI'});
  if(await explain.isVisible()) { await expect(explain).toBeEnabled({timeout:180000}); await explain.click(); }
  await expect(page.getByText('Suggested next step',{exact:true})).toBeVisible({timeout:210000});
  await page.screenshot({path:'demo/assets/screenshots/03-local-ai.png'});
  await page.getByRole('button',{name:'Create action draft'}).click();
  await expect(page.getByRole('heading',{name:'Fix queue',exact:true})).toBeVisible();
  const review=page.getByRole('button',{name:'Review & decide'}).first();
  if(await review.isVisible()) {await review.click();await page.getByRole('button',{name:'Approve for export',exact:true}).click();}
  await expect(page.getByText('approved',{exact:true}).first()).toBeVisible();
  const downloadPromise=page.waitForEvent('download');
  await page.getByRole('link',{name:'Export approved drafts'}).click();
  const download=await downloadPromise;
  expect(download.suggestedFilename()).toBe('quietops-approved-drafts.md');
  await page.screenshot({path:'demo/assets/screenshots/04-approved.png',fullPage:true});
  await page.getByRole('button',{name:'Inventory',exact:true}).click();
  await expect(page.getByRole('heading',{name:'60 products'})).toBeVisible();
  await page.getByLabel('Search inventory').fill('Oat milk');
  await expect(page.getByRole('cell',{name:'SKU-001',exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Suppliers',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Northfield Foods',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Audit history',exact:true}).click();
  await expect(page.getByText('Draft approved',{exact:true}).first()).toBeVisible();
  expect(errors).toEqual([]);
});

test('CSV import, deliberate mapping, quarantine and separate correction',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Upload spreadsheet').setInputFiles({name:'quality-review-test.csv',mimeType:'text/csv',buffer:Buffer.from('sku,date,qty,unit\nTEST-ONLY,2026-10-20,-7,each\n')});
  await expect(page.getByRole('heading',{name:'Make sure we’re on the same page.'})).toBeVisible();
  await page.getByRole('button',{name:'Confirm mapping & validate'}).click();
  await page.getByRole('button',{name:'Quality review',exact:true}).click();
  await expect(page.getByText('quality-review-test.csv · C2',{exact:true}).first()).toBeVisible();
  await page.getByRole('button',{name:'Propose correction'}).first().click();
  await page.getByLabel('Proposed value',{exact:true}).fill('7');
  await page.getByLabel('Reason',{exact:true}).fill('Synthetic browser test: verified quantity sign.');
  await page.getByRole('button',{name:'Save proposed correction'}).click();
  await expect(page.getByRole('status')).toContainText('Correction proposed');
});

test('mobile navigation and all views fit without horizontal page overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  for(const name of ['Issue inbox','Fix queue','Inventory','Suppliers','Import & mapping','Quality review','Audit history','Overview']) {
    await page.getByRole('button',{name:'Open navigation'}).click();
    await page.getByRole('button',{name,exact:true}).click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  }
  await page.screenshot({path:'demo/assets/screenshots/05-mobile.png',fullPage:true});
});
