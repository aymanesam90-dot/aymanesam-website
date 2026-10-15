import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const cases = [
  { name: 'small-mobile', width: 320, height: 700 },
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
];
const pages = ['index', 'experience', 'certifications', 'insights', 'contact'];
const browser = await chromium.launch({ headless: true });
const errors = [];
for (const lang of ['ar', 'en']) {
  for (const pageName of pages) {
    for (const viewport of cases) {
      const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      const url = `http://127.0.0.1:8765/${lang}/${pageName}.html`;
      const response = await page.goto(url, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const info = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        heading: document.querySelector('h1')?.textContent?.trim() || '',
      }));
      if (!response?.ok()) errors.push(`${url}: HTTP ${response?.status()}`);
      if (info.scrollWidth > info.clientWidth + 2) errors.push(`${lang}/${pageName} ${viewport.name}: horizontal overflow ${info.scrollWidth} > ${info.clientWidth}`);
      if (!info.heading) errors.push(`${lang}/${pageName}: missing h1`);
      if (viewport.width <= 390) {
        const menu = page.locator('.menu-toggle');
        const links = page.locator('#site-links');
        if (await menu.count()) {
          if (await menu.getAttribute('aria-expanded') !== 'false') errors.push(`${lang}/${pageName} ${viewport.name}: menu not initially collapsed`);
          await menu.click();
          if (await menu.getAttribute('aria-expanded') !== 'true' || !(await links.evaluate(el => el.classList.contains('open')))) {
            errors.push(`${lang}/${pageName} ${viewport.name}: menu failed to open`);
          }
          await menu.click();
          if (await menu.getAttribute('aria-expanded') !== 'false' || await links.evaluate(el => el.classList.contains('open'))) {
            errors.push(`${lang}/${pageName} ${viewport.name}: menu failed to close`);
          }
        }
      }
      const filename = path.join('responsive-results', lang, `${pageName}-${viewport.name}.png`);
      fs.mkdirSync(path.dirname(filename), { recursive: true });
      await page.screenshot({ path: filename, fullPage: true, animations: 'disabled' });
      console.log(`${lang}/${pageName} ${viewport.name}: ${info.scrollWidth}/${info.clientWidth} ${response?.status()}`);
      await page.close();
    }
  }
}
await browser.close();
console.log(`Captured ${2 * pages.length * cases.length} screenshots.`);
for (const error of errors) console.error('ERROR:', error);
if (errors.length) process.exitCode = 1;
