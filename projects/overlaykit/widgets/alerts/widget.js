/*@@LIB@@*/
// StreamElements custom widget: queued, themed alerts for follows, subs, gifts, tips, cheers and raids.
(function () {
  var Overlay = window.Overlay;
  var LISTENERS = { 'follower-latest': 'follower', 'subscriber-latest': 'subscriber', 'tip-latest': 'tip', 'cheer-latest': 'cheer', 'raid-latest': 'raid' };
  var ICONS = { follower: '♥', subscriber: '★', gift: '🎁', tip: '$', cheer: '◆', raid: '⚑' };
  var fd = {};
  var queue = null;
  var box;

  function templates() {
    var t = {};
    Object.keys(Overlay.DEFAULT_TEMPLATES).forEach(function (k) {
      var d = Overlay.DEFAULT_TEMPLATES[k];
      t[k] = { title: fd[k + 'Title'] || d.title, message: fd[k + 'Text'] || d.message };
    });
    return t;
  }

  function show(a, done) {
    document.getElementById('icon').textContent = ICONS[a.kind] || '!';
    document.getElementById('atitle').innerHTML = a.title;
    document.getElementById('amsg').innerHTML = a.message;
    document.getElementById('auser').innerHTML = fd.showMessages === 'no' ? '' : a.userMessage;
    if (fd.alertSound) {
      try { var s = new Audio(fd.alertSound); s.volume = (Number(fd.volume) || 50) / 100; s.play(); } catch (e) { /* autoplay blocked */ }
    }
    box.classList.add('show');
    setTimeout(function () { box.classList.remove('show'); setTimeout(done, 700); }, (Number(fd.duration) || 6) * 1000);
  }

  window.addEventListener('onWidgetLoad', function (obj) {
    fd = (obj && obj.detail && obj.detail.fieldData) || {};
    box = document.getElementById('alert');
    queue = new Overlay.AlertQueue(show);
  });

  window.addEventListener('onEventReceived', function (obj) {
    var d = obj && obj.detail;
    if (!d || !queue) return;
    var type = LISTENERS[d.listener];
    if (!type || fd['enable_' + type] === 'no') return;
    var ev = d.event || {};
    if (type === 'cheer' && Number(ev.amount) < (Number(fd.minBits) || 1)) return;
    if (type === 'tip' && Number(ev.amount) < (Number(fd.minTip) || 0)) return;
    var a = Overlay.formatAlert(type, ev, templates(), { currency: fd.currency || '$' });
    if (a) queue.push(a);
  });
})();
