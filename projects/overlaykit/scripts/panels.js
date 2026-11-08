// Twitch/YouTube profile panels as SVG (320x100, Twitch's panel width).
const { escapeHtml } = require('../overlays/lib.js');

const ICONS = {
  about: 'M50 30a12 12 0 1 1 0 24a12 12 0 1 1 0-24zM28 78c2-14 12-20 22-20s20 6 22 20z',
  schedule: 'M26 30h48v44H26zM26 42h48M38 24v12M62 24v12',
  rules: 'M32 24h36v52H32zM40 38h20M40 48h20M40 58h14',
  discord: 'M30 34q20-10 40 0l6 34q-10 8-18 8l-3-6q-5 2-10 0l-3 6q-8 0-18-8zM42 52a4 4 0 1 0 0.1 0M58 52a4 4 0 1 0 0.1 0',
  donate: 'M50 74L28 52a12 12 0 0 1 22-16a12 12 0 0 1 22 16z',
  setup: 'M24 30h52v34H24zM44 64v8M34 74h32',
  socials: 'M36 50a8 8 0 1 0 0.1 0M64 32a8 8 0 1 0 0.1 0M64 68a8 8 0 1 0 0.1 0M43 46l14-10M43 54l14 10',
  merch: 'M34 28l-12 10 8 10 6-4v32h28V44l6 4 8-10-12-10h-8a8 8 0 0 1-16 0z',
};

const DEFAULT_PANELS = ['about', 'schedule', 'rules', 'discord', 'donate', 'setup', 'socials', 'merch'];

function panelSvg({ label, icon, theme, width = 320, height = 100 }) {
  const path = ICONS[icon] || ICONS.about;
  const gid = `g${Math.abs([...label + icon].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7))}`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <linearGradient id="${gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${theme.accent}"/><stop offset="1" stop-color="${theme.accent2}"/></linearGradient>
    <style>@import url('https://fonts.googleapis.com/css2?family=${encodeURIComponent(theme.font).replace(/%20/g, '+')}:wght@700&amp;display=swap');</style>
  </defs>
  <rect x="2" y="2" width="${width - 4}" height="${height - 4}" rx="14" fill="${theme.panel}" stroke="url(#${gid})" stroke-width="3"/>
  <rect x="10" y="10" width="80" height="80" rx="12" fill="url(#${gid})"/>
  <path d="${path}" transform="translate(0,0)" fill="none" stroke="${theme.bg}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
  <text x="${(width + 90) / 2}" y="${height / 2 + 11}" text-anchor="middle" font-family="'${escapeHtml(theme.font)}', 'Arial Black', sans-serif" font-weight="700" font-size="30" letter-spacing="2" fill="${theme.text}">${escapeHtml(label.toUpperCase())}</text>
</svg>
`;
}

module.exports = { panelSvg, ICONS, DEFAULT_PANELS };
