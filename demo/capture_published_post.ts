import { chromium, expect } from '@playwright/test';
import { writeFile } from 'node:fs/promises';

const url = 'https://dev.to/saif-uk/i-built-a-local-ai-to-turn-a-shops-evening-spreadsheet-hunt-into-a-fix-queue-5b5p';

async function main() {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, deviceScaleFactor: 1 });
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await expect(page.getByRole('heading', { level: 1, name: "I Built a Local AI to Turn a Shop's Evening Spreadsheet Hunt Into a Fix Queue", exact: true })).toBeVisible();
    const article = page.locator('#article-body');
    await expect(article).toBeVisible();
    const images = article.locator('img[src*="media2.dev.to"]');
    expect(await images.count()).toBe(5);
    for (const image of await images.all()) {
      await image.scrollIntoViewIfNeeded();
      await expect(image).toHaveJSProperty('complete', true, { timeout: 30000 });
      await expect(image).not.toHaveJSProperty('naturalWidth', 0);
    }
    await expect(article.locator('iframe[src="https://www.youtube.com/embed/NclbnG0_8d0"]')).toHaveCount(1);
    await expect(article.locator('a[href="https://github.com/Saifullahakjsnd/QuietOps"]').first()).toBeAttached();
    await page.evaluate(() => window.scrollTo(0, 0));
    const dismissBillboard = page.getByRole('button', { name: 'Dismiss billboard', exact: true });
    if (await dismissBillboard.isVisible()) await dismissBillboard.click();
    await page.screenshot({ path: 'demo/assets/screenshots/09-published-dev-post.png' });
    const report = { url, verified_at: new Date().toISOString(), browser: 'Microsoft Edge / Playwright', article_images_loaded: 5, youtube_embed_present: true, github_link_present: true, screenshot: 'demo/assets/screenshots/09-published-dev-post.png' };
    await writeFile('docs/dev-publication-verification.json', JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
