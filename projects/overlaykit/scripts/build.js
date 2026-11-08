// Build sellable packs: one folder (and zip) per theme, plus PNG previews for store listings.
//   node scripts/build.js            -> dist/
//   node scripts/build.js --no-png   -> skip Chromium rendering
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { panelSvg, DEFAULT_PANELS } = require('./panels.js');
const { buildWidget } = require('./streamelements.js');

const root = path.join(__dirname, '..');
const dist = path.join(root, 'dist');
const themes = JSON.parse(fs.readFileSync(path.join(root, 'themes.json'), 'utf8'));
const wantPng = !process.argv.includes('--no-png');

function writeThemesJs() {
  const js = `/* Generated from themes.json by scripts/build.js. */\nwindow.OVERLAY_THEMES = ${JSON.stringify(themes, null, 2)};\n`;
  fs.writeFileSync(path.join(root, 'overlays', 'themes.js'), js);
}

const SCENES = [
  { file: 'starting-soon.html', w: 1920, h: 1080, query: 'minutes=5&socials=twitch:yourname,x:yourname&messages=Grab a drink|Turn on notifications' },
  { file: 'brb.html', w: 1920, h: 1080, query: 'socials=discord:yourserver' },
  { file: 'ending.html', w: 1920, h: 1080, query: 'subtitle=Raiding someone awesome next&socials=youtube:@yourname' },
  { file: 'alerts.html', w: 1920, h: 400, query: 'demo=1', transparent: true },
  { file: 'lower-third.html', w: 1920, h: 1080, query: 'name=YourName&messages=Now playing: ranked grind', transparent: true },
  { file: 'webcam-frame.html', w: 700, h: 430, query: 'name=YourName', transparent: true },
];

function setupGuide(key, theme) {
  const lines = SCENES.map((s) => `  ${s.file.padEnd(20)} file:///PATH/TO/overlays/${s.file}?theme=${key}&${s.query.replace(/ /g, '%20')}  (${s.w}x${s.h})`);
  return `${theme.label} overlay pack — setup
==========================================

OBS: Sources → + → Browser. Leave "Local file" UNticked (it drops the URL parameters),
paste the URL below into "URL" (replace PATH/TO with the folder you unzipped this pack to;
on Windows it looks like file:///C:/Users/you/overlaykit-neon/overlays/...) and set width/height.

${lines.join('\n')}

Customise any scene with URL parameters:
  title=, subtitle=        text
  socials=twitch:name,x:name,youtube:@name,discord:invite
  messages=one|two|three   rotating ticker / lower-third lines
  minutes=10 or until=19:30 (starting-soon countdown)
  accent=ff00aa&accent2=00ffcc   override colours (hex, no #)
  w=640&h=360, name=        webcam frame size and name tag

Live alerts (StreamElements):
  1. streamelements.com → Streaming tools → Overlays → New overlay → + → Static/Custom → Custom widget
  2. Open Settings → Open editor. Paste each file from streamelements-alerts/ into the
     matching HTML / CSS / JS / FIELDS / DATA tab. Save.
  3. Add the overlay URL to OBS as a Browser source (1920x1080).
  4. Use "Emulate" in the editor to fire test alerts.

Twitch panels: upload panels/png/*.png (320x100) in your channel's About section.
`;
}

const LICENSE = `License — personal & commercial streaming use
You may use these overlays on any number of your own channels, including monetised
streams and VODs. You may edit them. You may not resell, share or redistribute the
files (modified or not) or include them in another product for sale.
`;

async function renderPngs(jobs) {
  let chromium;
  try { ({ chromium } = require('playwright')); } catch { return false; }
  const browser = await chromium.launch();
  try {
    for (const j of jobs) {
      const page = await browser.newPage({ viewport: { width: j.w, height: j.h } });
      await page.goto(j.url, { waitUntil: 'load' });
      // Store previews: show transparent overlays on a dark, stream-like backdrop.
      if (j.previewBg) await page.addStyleTag({ content: 'html,body{background:#1d1d24 !important}' });
      await page.waitForTimeout(j.wait ?? 1200);
      await page.screenshot({ path: j.out, omitBackground: !!j.transparent });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  return true;
}

async function main() {
  writeThemesJs();
  fs.rmSync(dist, { recursive: true, force: true });
  fs.mkdirSync(dist, { recursive: true });
  const pngJobs = [];
  const gallery = [];

  for (const [key, theme] of Object.entries(themes)) {
    const pack = path.join(dist, `overlaykit-${key}`);
    fs.cpSync(path.join(root, 'overlays'), path.join(pack, 'overlays'), { recursive: true });
    buildWidget(theme, path.join(pack, 'streamelements-alerts'));
    fs.mkdirSync(path.join(pack, 'panels', 'png'), { recursive: true });
    fs.mkdirSync(path.join(pack, 'previews'), { recursive: true });
    for (const name of DEFAULT_PANELS) {
      const svgPath = path.join(pack, 'panels', `${name}.svg`);
      fs.writeFileSync(svgPath, panelSvg({ label: name, icon: name, theme }));
      pngJobs.push({ url: `file://${svgPath}`, out: path.join(pack, 'panels', 'png', `${name}.png`), w: 320, h: 100, wait: 600 });
    }
    for (const s of SCENES) {
      const url = `file://${path.join(pack, 'overlays', s.file)}?theme=${key}&${s.query}`;
      const out = path.join(pack, 'previews', s.file.replace('.html', '.png'));
      pngJobs.push({ url, out, w: s.w, h: s.h, wait: s.file === 'alerts.html' ? 1500 : 1200, previewBg: !!s.transparent });
      gallery.push({ key, label: theme.label, scene: s.file, img: path.relative(dist, out) });
    }
    fs.writeFileSync(path.join(pack, 'OBS-SETUP.txt'), setupGuide(key, theme));
    fs.writeFileSync(path.join(pack, 'LICENSE.txt'), LICENSE);
  }

  const rendered = wantPng && (await renderPngs(pngJobs));
  if (!rendered) console.log(wantPng ? 'playwright not found: skipped PNG panels/previews (SVGs are included).' : 'Skipped PNG rendering.');

  fs.writeFileSync(path.join(dist, 'gallery.html'), `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OverlayKit gallery</title>
<style>body{font-family:system-ui;background:#111;color:#eee;margin:0;padding:16px}h2{margin-top:32px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}img{width:100%;border-radius:8px;background:repeating-conic-gradient(#222 0 25%,#2a2a2a 0 50%) 0 0/20px 20px}</style>
${Object.entries(themes).map(([k, t]) => `<h2>${t.label}</h2><div class="g">${gallery.filter((g) => g.key === k).map((g) => `<figure><img src="${g.img}" alt="${g.scene}" loading="lazy"><figcaption>${g.scene}</figcaption></figure>`).join('')}</div>`).join('')}`);

  // Zip each pack if the zip CLI exists (it does on macOS and most Linux).
  for (const key of Object.keys(themes)) {
    try {
      execFileSync('zip', ['-qr', `overlaykit-${key}.zip`, `overlaykit-${key}`], { cwd: dist });
    } catch {
      console.log('zip not available: packs left as folders.');
      break;
    }
  }
  console.log(`Built ${Object.keys(themes).length} theme packs in ${dist}${rendered ? ' (with PNG previews)' : ''}.`);
}

main().catch((e) => { console.error(e); process.exit(1); });
