import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const cases = [
  { name: 'small-mobile', width: 320, height: 700 },
  { name: 'mobile', width: 390, height: 844 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
];
const pages = ['index', 'about', 'expertise', 'experience', 'education', 'certifications', 'insights', 'contact'];
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
      if (viewport.width === 390) {
        const skip = page.locator('a.skip-link[href="#main"]');
        if (await skip.count() !== 1 || !(await page.locator('main#main').count())) {
          errors.push(`${lang}/${pageName}: missing accessible skip link or main target`);
        } else {
          await page.keyboard.press('Tab');
          if (!(await skip.evaluate(el => el === document.activeElement))) {
            errors.push(`${lang}/${pageName}: skip link is not first keyboard focus target`);
          } else {
            await page.keyboard.press('Enter');
            if (new URL(page.url()).hash !== '#main') {
              errors.push(`${lang}/${pageName}: skip link Enter did not navigate to main`);
            }
          }
        }
      }

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
      if (pageName === 'index' && viewport.width === 1440) {
        await page.emulateMedia({ reducedMotion: 'reduce' });
        const carousel = page.locator('.client-carousel-viewport');
        const next = page.locator('.client-next');
        const prev = page.locator('.client-prev');
        if (await carousel.count() && await next.count() && await prev.count()) {
          await carousel.evaluate(el => { el.scrollLeft = 0; });
          await page.waitForTimeout(100);
          const before = await carousel.evaluate(el => el.scrollLeft);
          await next.click();
          const afterNext = await carousel.evaluate(el => el.scrollLeft);
          if (Math.abs(afterNext - before) < 5) errors.push(`${lang}/index: next carousel control did not move while reduced motion enabled`);
          await prev.click();
          const afterPrev = await carousel.evaluate(el => el.scrollLeft);
          if (Math.abs(afterPrev - afterNext) < 5) errors.push(`${lang}/index: previous carousel control did not move while reduced motion enabled`);
        }
      }
      if (viewport.width === 390 && ['index', 'contact'].includes(pageName)) {
        const switcher = page.locator(`a[href="../${lang === 'ar' ? 'en' : 'ar'}/${pageName}.html"]`);
        if (await switcher.count() !== 1) {
          errors.push(`${lang}/${pageName}: expected one language switch link to equivalent page`);
        } else {
          const target = await switcher.getAttribute('href');
          const expectedLang = lang === 'ar' ? 'en' : 'ar';
          const resolved = new URL(target, url);
          const languageResponse = await page.request.get(resolved.href);
          if (!languageResponse.ok()) errors.push(`${lang}/${pageName}: language switch target returned HTTP ${languageResponse.status()}`);
          const targetHtml = await languageResponse.text();
          if (!new RegExp(`<html[^>]+lang=["']${expectedLang}["']`, 'i').test(targetHtml)) {
            errors.push(`${lang}/${pageName}: language switch target has incorrect html lang`);
          }
        }
      }
      if (pageName === 'contact' && viewport.width === 390) {
        const email = page.locator('a[href^="mailto:"]');
        const phone = page.locator('a[href^="tel:"]');
        if (!(await email.count())) errors.push(`${lang}/contact: no actionable email link`);
        if (!(await phone.count())) errors.push(`${lang}/contact: no actionable phone link`);
        for (const link of [email.first(), phone.first()]) {
          if (await link.count()) {
            const href = await link.getAttribute('href');
            if (!href || /\\s/.test(href) || /^(mailto:|tel:)$/.test(href)) errors.push(`${lang}/contact: invalid contact action ${href}`);
          }
        }
      }
      if (viewport.width === 390) {
        const nav = page.locator('#site-links');
        const expectedPages = ['index', 'about', 'expertise', 'experience', 'education', 'certifications', 'insights', 'contact'];
        if (await nav.count()) {
          for (const target of expectedPages) {
            const link = nav.locator(`a[href="${target}.html"]`);
            if (await link.count() !== 1) {
              errors.push(`${lang}/${pageName}: expected one mobile navigation link to ${target}.html`);
            } else {
              const destination = new URL(`${target}.html`, url);
              const destinationResponse = await page.request.get(destination.href);
              if (!destinationResponse.ok()) errors.push(`${lang}/${pageName}: navigation target ${target}.html returned HTTP ${destinationResponse.status()}`);
            }
          }
        } else {
          errors.push(`${lang}/${pageName}: mobile navigation links container missing`);
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
// Audit every bilingual article at small/mobile widths as well as the five primary pages.
const articleSlugs = [
  'cash-flow-liquidity-rhythm',
  'fp-and-a-for-better-decisions',
  'cash-flow-discipline',
  'finance-transformation',
  'budgeting-as-management-system',
  'working-capital-discipline',
  'month-end-close-discipline',
];
let articleScreenshots = 0;
for (const lang of ['ar', 'en']) {
  for (const slug of articleSlugs) {
    for (const viewport of cases.filter(v => v.width <= 390)) {
      const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height }, deviceScaleFactor: 1 });
      const url = `http://127.0.0.1:8765/${lang}/insights/${slug}.html`;
      const response = await page.goto(url, { waitUntil: 'networkidle' });
      await page.evaluate(() => document.fonts.ready);
      const info = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        heading: document.querySelector('h1')?.textContent?.trim() || '',
        lang: document.documentElement.lang,
        main: !!document.querySelector('main'),
      }));
      if (!response?.ok()) errors.push(`${lang}/insights/${slug}: HTTP ${response?.status()}`);
      if (info.scrollWidth > info.clientWidth + 2) errors.push(`${lang}/insights/${slug} ${viewport.name}: horizontal overflow ${info.scrollWidth} > ${info.clientWidth}`);
      if (!info.heading) errors.push(`${lang}/insights/${slug}: missing h1`);
      if (info.lang !== lang) errors.push(`${lang}/insights/${slug}: incorrect document language ${info.lang}`);
      if (!info.main) errors.push(`${lang}/insights/${slug}: missing main landmark`);
      if (viewport.width === 390) {
        const skip = page.locator('a.skip-link[href="#main"]');
        if (await skip.count() !== 1) errors.push(`${lang}/insights/${slug}: missing skip-to-content link`);
        else if (!(await page.locator('main#main').count())) errors.push(`${lang}/insights/${slug}: skip link target missing`);
        else {
          await page.keyboard.press('Tab');
          if (!(await skip.evaluate(el => el === document.activeElement))) {
            errors.push(`${lang}/insights/${slug}: skip link is not first keyboard focus target`);
          } else {
            await page.keyboard.press('Enter');
            if (new URL(page.url()).hash !== '#main') {
              errors.push(`${lang}/insights/${slug}: skip link keyboard activation did not navigate to main`);
            }
          }
        }
      }
      if (viewport.width === 390) {
        const seo = await page.evaluate(() => ({
          title: document.title.trim(),
          description: document.querySelector('meta[name="description"]')?.content?.trim() || '',
          canonical: document.querySelector('link[rel="canonical"]')?.href || '',
          alternates: Array.from(document.querySelectorAll('link[rel="alternate"][hreflang]')).map(el => ({ lang: el.hreflang, href: el.href })),
        }));
        if (!seo.title) errors.push(`${lang}/insights/${slug}: missing page title`);
        if (!seo.description) errors.push(`${lang}/insights/${slug}: missing meta description`);
        const social = await page.evaluate(() => ({
          ogTitle: document.querySelector('meta[property="og:title"]')?.content?.trim() || '',
          ogDescription: document.querySelector('meta[property="og:description"]')?.content?.trim() || '',
          ogUrl: document.querySelector('meta[property="og:url"]')?.content || '',
          ogImage: document.querySelector('meta[property="og:image"]')?.content || '',
          twitterCard: document.querySelector('meta[name="twitter:card"]')?.content || '',
          twitterImage: document.querySelector('meta[name="twitter:image"]')?.content || '',
        }));
        const canonical = `https://aymanesam.com/${lang}/insights/${slug}`;
        if (!social.ogTitle || !social.ogDescription) errors.push(`${lang}/insights/${slug}: missing Open Graph title or description`);
        if (social.ogUrl !== canonical) errors.push(`${lang}/insights/${slug}: Open Graph URL does not match canonical`);
        if (!social.ogImage.startsWith('https://') || !social.twitterImage.startsWith('https://')) {
          errors.push(`${lang}/insights/${slug}: social preview image URL must be HTTPS`);
        }
        if (!social.twitterCard) errors.push(`${lang}/insights/${slug}: missing Twitter card type`);
        for (const [kind, imageUrl] of [['Open Graph', social.ogImage], ['Twitter', social.twitterImage]]) {
          if (imageUrl.startsWith('https://aymanesam.com/assets/')) {
            const assetUrl = new URL(imageUrl);
            const localAsset = `http://127.0.0.1:8765${assetUrl.pathname}`;
            const assetResponse = await page.request.get(localAsset);
            if (!assetResponse.ok()) errors.push(`${lang}/insights/${slug}: ${kind} image asset returned HTTP ${assetResponse.status()}`);
            else if (!(assetResponse.headers()['content-type'] || '').startsWith('image/')) {
              errors.push(`${lang}/insights/${slug}: ${kind} image asset is not served as an image`);
            }
          }
        }


        if (seo.canonical !== canonical) errors.push(`${lang}/insights/${slug}: unexpected canonical ${seo.canonical}`);
        for (const translatedLang of ['ar', 'en']) {
          const expected = `https://aymanesam.com/${translatedLang}/insights/${slug}`;
          if (!seo.alternates.some(a => a.lang === translatedLang && a.href === expected)) {
            errors.push(`${lang}/insights/${slug}: missing ${translatedLang} hreflang alternate`);
          }
        }
      }
      if (viewport.width === 390) {
        const otherLang = lang === 'ar' ? 'en' : 'ar';
        const expectedHref = `../../${otherLang}/insights/${slug}.html`;
        const switcher = page.locator(`a[href="${expectedHref}"]`);
        if (await switcher.count() !== 1) {
          errors.push(`${lang}/insights/${slug}: expected exactly one language switch to corresponding article`);
        } else {
          const destination = new URL(expectedHref, url);
          const translated = await page.request.get(destination.href);
          if (!translated.ok()) errors.push(`${lang}/insights/${slug}: translated article HTTP ${translated.status()}`);
          else if (!new RegExp(`<html[^>]+lang=["']${otherLang}["']`, 'i').test(await translated.text())) {
            errors.push(`${lang}/insights/${slug}: translated article language is incorrect`);
          }
        }
        const back = page.locator('a[href="../insights.html"]');
        if (!(await back.count())) errors.push(`${lang}/insights/${slug}: missing link back to insights index`);
      }
      if (viewport.width === 390) {
        const menu = page.locator('.menu-toggle');
        const links = page.locator('#site-links');
        if (await menu.count() !== 1 || await links.count() !== 1) {
          errors.push(`${lang}/insights/${slug}: mobile menu controls missing`);
        } else {
          if (await menu.getAttribute('aria-expanded') !== 'false') errors.push(`${lang}/insights/${slug}: menu initially expanded`);
          await menu.focus();
          await page.keyboard.press('Enter');
          if (await menu.getAttribute('aria-expanded') !== 'true' || !(await links.evaluate(el => el.classList.contains('open')))) {
            errors.push(`${lang}/insights/${slug}: keyboard Enter failed to open mobile menu`);
          }
          await page.keyboard.press('Enter');
          if (await menu.getAttribute('aria-expanded') !== 'false' || await links.evaluate(el => el.classList.contains('open'))) {
            errors.push(`${lang}/insights/${slug}: keyboard Enter failed to close mobile menu`);
          }
        }
      }
      const filename = path.join('responsive-results', lang, 'articles', `${slug}-${viewport.name}.png`);
      fs.mkdirSync(path.dirname(filename), { recursive: true });
      await page.screenshot({ path: filename, fullPage: true, animations: 'disabled' });
      articleScreenshots++;
      await page.close();
    }
  }
}
console.log(`Captured ${articleScreenshots} additional bilingual article screenshots.`);
await browser.close();
console.log(`Captured ${2 * pages.length * cases.length} screenshots.`);
for (const error of errors) console.error('ERROR:', error);
if (errors.length) process.exitCode = 1;
