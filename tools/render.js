// Render the site and photograph it, because a page is not done until it has been looked at.
//
// ⚠️ A FRESH USER DATA DIR EVERY RUN. Headless Chrome will happily serve a cached copy of the
// previous build and hand back a screenshot of work you have already replaced - a trap this
// machine has fallen into before with PDF rendering.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const os = require('os');
const path = require('path');

const SITE = process.env.SITE_URL || 'http://127.0.0.1:8899/';
const OUT = process.env.OUT_DIR;

(async () => {
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'render-'));
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH,
    headless: 'new',
    userDataDir: profile,
    args: ['--no-first-run', '--no-default-browser-check', '--disable-lcd-text'],
  });

  for (const [label, w, h] of [['desktop', 1280, 1000], ['phone', 412, 900]]) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 2 });
    await page.goto(SITE, { waitUntil: 'networkidle0', timeout: 60000 });
    // Lazy images do not load until they scroll in, and a screenshot of empty boxes proves nothing.
    await page.evaluate(async () => {
      await new Promise(r => {
        let y = 0;
        const t = setInterval(() => {
          window.scrollBy(0, 400); y += 400;
          if (y > document.body.scrollHeight) { clearInterval(t); window.scrollTo(0, 0); r(); }
        }, 40);
      });
    });
    await new Promise(r => setTimeout(r, 1500));

    // ⚠️ REPORT BROKEN IMAGES AND HORIZONTAL OVERFLOW. Both look fine in the markup and wrong on
    // screen, and both are invisible in a full-page capture that has already scaled everything.
    const problems = await page.evaluate(() => {
      const broken = [...document.images]
        .filter(i => !i.complete || i.naturalWidth === 0)
        .map(i => i.getAttribute('src'));
      return { broken, docW: document.documentElement.scrollWidth, winW: window.innerWidth };
    });
    if (problems.broken.length) console.log(`  ${label}: BROKEN IMAGES ${JSON.stringify(problems.broken)}`);
    if (problems.docW > problems.winW + 1) console.log(`  ${label}: HORIZONTAL OVERFLOW ${problems.docW} > ${problems.winW}`);

    await page.screenshot({ path: `${OUT}/${label}.png`, fullPage: true });
    console.log(`  ${label}.png  page ${problems.docW}px in a ${problems.winW}px window, ${problems.broken.length} broken images`);
    await page.close();
  }
  await browser.close();
  fs.rmSync(profile, { recursive: true, force: true });
})().catch(e => { console.error('FAILED:', e.message); process.exit(1); });
