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
      if (viewport.width <= 390) {
        const menu = page.locator('.menu-toggle');
        const links = page.locator('#site-links');
        if (await menu.count()) {
          await menu.focus();
          if (!(await menu.evaluate(el => el === document.activeElement))) errors.push(`${lang}/${pageName} ${viewport.name}: menu not keyboard focusable`);
          await page.keyboard.press('Enter');
          if (await menu.getAttribute('aria-expanded') !== 'true') errors.push(`${lang}/${pageName} ${viewport.name}: Enter failed to open menu`);
          if (await links.count()) {
            const firstLink = links.locator('a').first();
            await firstLink.focus();
            if (!(await firstLink.evaluate(el => el === document.activeElement))) errors.push(`${lang}/${pageName} ${viewport.name}: navigation link not keyboard focusable`);
          }
          await menu.focus();
          await page.keyboard.press('Space');
          if (await menu.getAttribute('aria-expanded') !== 'false') errors.push(`${lang}/${pageName} ${viewport.name}: Space failed to close menu`);
        }
      }
      if (pageName === 'index' && viewport.width === 390) {
        await page.emulateMedia({ reducedMotion: 'reduce' });
        const carousel = page.locator('.client-carousel-viewport');
        if (await carousel.count()) {
          await carousel.evaluate(el => { el.scrollLeft = 0; });
          await page.waitForTimeout(350);
          const start = await carousel.evaluate(el => el.scrollLeft);
          await page.waitForTimeout(450);
          const end = await carousel.evaluate(el => el.scrollLeft);
          if (Math.abs(end - start) > 2) {
            errors.push(`${lang}/index: carousel auto-scrolls despite reduced-motion preference (${start} -> ${end})`);
          }
        }
      }
      if (pageName === 'index' && viewport.width === 1440) {
        const section = page.locator('.client-section');
        const carousel = page.locator('.client-carousel-viewport');
        if (await section.count() && await carousel.count()) {
          const read = () => carousel.evaluate(el => el.scrollLeft);
          await section.hover();
          await page.waitForTimeout(150);
          const hoverStart = await read();
          await page.waitForTimeout(350);
          const hoverEnd = await read();
          if (Math.abs(hoverEnd - hoverStart) > 2) errors.push(`${lang}/index: carousel moves while hovered (${hoverStart} -> ${hoverEnd})`);
          await page.mouse.move(0, 0);
          const next = section.locator('.client-next');
          if (await next.count()) {
            await next.focus();
            await page.waitForTimeout(150);
            const focusStart = await read();
            await page.waitForTimeout(350);
            const focusEnd = await read();
            if (Math.abs(focusEnd - focusStart) > 2) errors.push(`${lang}/index: carousel moves during keyboard focus (${focusStart} -> ${focusEnd})`);
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
