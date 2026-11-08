// Builds per-theme StreamElements widget files (fields.json defaults come from the theme).
const fs = require('node:fs');
const path = require('node:path');

const yesNo = (label, group) => ({ type: 'dropdown', label, value: 'yes', options: { yes: 'Yes', no: 'No' }, group });

function fieldsFor(theme) {
  const f = {
    duration: { type: 'number', label: 'Alert duration (seconds)', value: 6, min: 2, max: 30, group: 'General' },
    alertSound: { type: 'sound-input', label: 'Alert sound', value: '', group: 'General' },
    volume: { type: 'slider', label: 'Volume', value: 50, min: 0, max: 100, step: 1, group: 'General' },
    showMessages: { type: 'dropdown', label: 'Show viewer messages', value: 'yes', options: { yes: 'Yes', no: 'No' }, group: 'General' },
    currency: { type: 'text', label: 'Currency symbol', value: '$', group: 'General' },
    minBits: { type: 'number', label: 'Minimum bits', value: 1, group: 'General' },
    minTip: { type: 'number', label: 'Minimum tip', value: 0, group: 'General' },
    accentColor: { type: 'colorpicker', label: 'Accent', value: theme.accent, group: 'Colours' },
    accent2Color: { type: 'colorpicker', label: 'Accent 2', value: theme.accent2, group: 'Colours' },
    panelColor: { type: 'colorpicker', label: 'Panel', value: theme.panel, group: 'Colours' },
    textColor: { type: 'colorpicker', label: 'Text', value: theme.text, group: 'Colours' },
    mutedColor: { type: 'colorpicker', label: 'Muted text', value: theme.muted, group: 'Colours' },
    bgColor: { type: 'colorpicker', label: 'Icon text', value: theme.bg, group: 'Colours' },
    displayFont: { type: 'googleFont', label: 'Display font', value: theme.font, group: 'Fonts' },
    bodyFont: { type: 'googleFont', label: 'Body font', value: theme.body, group: 'Fonts' },
  };
  const defaults = require('../overlays/lib.js').DEFAULT_TEMPLATES;
  for (const [k, t] of Object.entries(defaults)) {
    if (k !== 'gift') f[`enable_${k === 'follower' ? 'follower' : k}`] = yesNo(`Enable ${k} alerts`, 'Alerts');
    f[`${k}Title`] = { type: 'text', label: `${k} title`, value: t.title, group: 'Text' };
    f[`${k}Text`] = { type: 'text', label: `${k} message`, value: t.message, group: 'Text' };
  }
  return f;
}

function buildWidget(theme, outDir) {
  const root = path.join(__dirname, '..');
  const src = (p) => fs.readFileSync(path.join(root, p), 'utf8');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'widget.html'), src('widgets/alerts/widget.html'));
  fs.writeFileSync(path.join(outDir, 'widget.css'), src('widgets/alerts/widget.css').replace('/*@@ALERTS_CSS@@*/', () => src('overlays/alerts.css')));
  fs.writeFileSync(path.join(outDir, 'widget.js'), src('widgets/alerts/widget.js').replace('/*@@LIB@@*/', () => src('overlays/lib.js')));
  fs.writeFileSync(path.join(outDir, 'fields.json'), JSON.stringify(fieldsFor(theme), null, 2));
  fs.writeFileSync(path.join(outDir, 'data.json'), '{}\n');
}

module.exports = { fieldsFor, buildWidget };
