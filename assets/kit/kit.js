/* SPAN 1001 site kit: theme toggle + full screen. Stores only the reader's light/dark choice. */
(function () {
  var root = document.documentElement, KEY = 'site:theme';
  try { var t = localStorage.getItem(KEY); if (t) root.setAttribute('data-theme', t); } catch (e) {}

  function isDark() {
    var t = root.getAttribute('data-theme');
    return t ? t === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  function label() {
    var b = document.getElementById('theme-btn');
    if (b) { b.textContent = isDark() ? 'Light mode' : 'Dark mode'; b.setAttribute('aria-pressed', isDark()); }
  }
  window.toggleTheme = function () {
    var next = isDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
    label();
  };
  window.toggleFS = function () {
    var d = document, el = d.documentElement;
    if (!(d.fullscreenElement || d.webkitFullscreenElement)) {
      (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el);
    } else {
      (d.exitFullscreen || d.webkitExitFullscreen).call(d);
    }
  };
  function fsLabel() {
    var b = document.getElementById('fs-btn');
    if (b) b.textContent = (document.fullscreenElement || document.webkitFullscreenElement) ? 'Exit full screen' : 'Full screen';
  }
  document.addEventListener('fullscreenchange', fsLabel);
  document.addEventListener('webkitfullscreenchange', fsLabel);
  document.addEventListener('DOMContentLoaded', function () {
    label();
    var fs = document.getElementById('fs-btn');
    if (fs && !(document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen)) fs.hidden = true;
  });
})();
