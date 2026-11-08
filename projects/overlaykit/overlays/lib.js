/* OverlayKit runtime. Plain script: works in OBS browser sources, StreamElements and Node (tests). */
(function (root) {
  var THEME_KEYS = ['bg', 'panel', 'text', 'muted', 'accent', 'accent2'];

  function parseParams(search) {
    var out = {};
    String(search || '').replace(/^\?/, '').split('&').forEach(function (pair) {
      if (!pair) return;
      var i = pair.indexOf('=');
      var k = decodeURIComponent((i < 0 ? pair : pair.slice(0, i)).replace(/\+/g, ' '));
      var v = i < 0 ? '' : decodeURIComponent(pair.slice(i + 1).replace(/\+/g, ' '));
      out[k] = v;
    });
    return out;
  }

  function isHexColor(s) { return /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.test(String(s || '')); }
  function normHex(s) { return s.charAt(0) === '#' ? s : '#' + s; }

  /** Merge a named theme with URL overrides (?accent=ff00aa&accent2=...). Unknown theme falls back to the first. */
  function resolveTheme(themes, params) {
    var names = Object.keys(themes);
    var base = themes[params.theme] || themes[names[0]];
    var t = {};
    for (var k in base) t[k] = base[k];
    THEME_KEYS.forEach(function (key) { if (isHexColor(params[key])) t[key] = normHex(params[key]); });
    return t;
  }

  /** "Starting in" countdown. `until` is HH:MM local time, else `minutes` from load. */
  function countdownTarget(params, now) {
    now = now || new Date();
    if (/^\d{1,2}:\d{2}$/.test(params.until || '')) {
      var parts = params.until.split(':');
      var d = new Date(now.getTime());
      d.setHours(Number(parts[0]), Number(parts[1]), 0, 0);
      if (d.getTime() <= now.getTime()) d.setDate(d.getDate() + 1);
      return d.getTime();
    }
    var mins = Number(params.minutes);
    return now.getTime() + (isFinite(mins) && mins > 0 ? mins : 5) * 60000;
  }

  function formatCountdown(ms) {
    if (ms <= 0) return '00:00';
    var s = Math.ceil(ms / 1000);
    var h = Math.floor(s / 3600);
    var m = Math.floor((s % 3600) / 60);
    var sec = s % 60;
    var pad = function (n) { return (n < 10 ? '0' : '') + n; };
    return h ? h + ':' + pad(m) + ':' + pad(sec) : pad(m) + ':' + pad(sec);
  }

  /** "twitch:name,x:name,youtube:@name" -> [{ platform, handle }] */
  function parseSocials(str) {
    return String(str || '').split(',').map(function (s) { return s.trim(); }).filter(Boolean).map(function (s) {
      var i = s.indexOf(':');
      return i < 0 ? { platform: 'link', handle: s } : { platform: s.slice(0, i).toLowerCase(), handle: s.slice(i + 1) };
    });
  }

  var DEFAULT_TEMPLATES = {
    follower: { title: 'New follower', message: '{name} just followed!' },
    subscriber: { title: 'New subscriber', message: '{name} subscribed{months}!' },
    gift: { title: 'Gifted sub', message: '{sender} gifted a sub to {name}!' },
    tip: { title: 'Tip', message: '{name} tipped {amount}!' },
    cheer: { title: 'Cheer', message: '{name} cheered {amount} bits!' },
    raid: { title: 'Raid', message: '{name} is raiding with {amount} viewers!' }
  };

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /**
   * Turn a StreamElements-style event into display text. Values are HTML-escaped:
   * viewer-controlled names must never inject markup into the overlay.
   */
  function formatAlert(type, event, templates, opts) {
    templates = templates || DEFAULT_TEMPLATES;
    opts = opts || {};
    event = event || {};
    var kind = type === 'subscriber' && event.gifted ? 'gift' : type;
    var tpl = templates[kind] || DEFAULT_TEMPLATES[kind];
    if (!tpl) return null;
    var amount = event.amount;
    if (type === 'tip') amount = (opts.currency || '$') + Number(amount || 0).toFixed(2);
    var months = type === 'subscriber' && Number(event.amount) > 1 ? ' for ' + Number(event.amount) + ' months' : '';
    var vals = { name: event.name || 'Someone', sender: event.sender || 'Someone', amount: amount == null ? '' : amount, months: months, message: event.message || '' };
    var fill = function (s) { return String(s).replace(/\{(\w+)\}/g, function (_, k) { return escapeHtml(vals[k] != null ? vals[k] : ''); }); };
    return { kind: kind, title: fill(tpl.title), message: fill(tpl.message), userMessage: escapeHtml(event.message || '') };
  }

  /** Simple FIFO so alerts never overlap. `show(alert, done)` must call done(). */
  function AlertQueue(show) {
    this.items = [];
    this.busy = false;
    this.show = show;
  }
  AlertQueue.prototype.push = function (a) { this.items.push(a); this.next(); };
  AlertQueue.prototype.next = function () {
    if (this.busy || !this.items.length) return;
    this.busy = true;
    var self = this;
    this.show(this.items.shift(), function () { self.busy = false; self.next(); });
  };

  function applyTheme(doc, theme) {
    var s = doc.documentElement.style;
    THEME_KEYS.forEach(function (k) { s.setProperty('--' + k, theme[k]); });
    s.setProperty('--font', "'" + theme.font + "', system-ui, sans-serif");
    s.setProperty('--body', "'" + theme.body + "', system-ui, sans-serif");
    var link = doc.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=' + [theme.font, theme.body].map(function (f) {
      return encodeURIComponent(f).replace(/%20/g, '+') + ':wght@400;600;700';
    }).join('&family=') + '&display=swap';
    doc.head.appendChild(link);
  }

  var api = {
    parseParams: parseParams, resolveTheme: resolveTheme, countdownTarget: countdownTarget,
    formatCountdown: formatCountdown, parseSocials: parseSocials, formatAlert: formatAlert,
    escapeHtml: escapeHtml, AlertQueue: AlertQueue, applyTheme: applyTheme, DEFAULT_TEMPLATES: DEFAULT_TEMPLATES
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Overlay = api;
})(typeof window !== 'undefined' ? window : this);
