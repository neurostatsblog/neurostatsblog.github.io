// neurostatsblog — main.js
// Dark mode toggle + scroll-aware header

(function () {
  'use strict';

  // ── Dark mode toggle ──────────────────────────────────────
  var toggle = document.querySelector('[data-theme-toggle]');
  var html   = document.documentElement;

  function getTheme() {
    var attr = html.getAttribute('data-theme');
    if (attr) return attr;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function setTheme(theme) {
    html.setAttribute('data-theme', theme);
    if (toggle) {
      toggle.setAttribute('aria-label', 'Switch to ' + (theme === 'dark' ? 'light' : 'dark') + ' mode');
    }
  }

  // Initialise from system preference (already set inline before paint)
  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = getTheme();
      setTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // ── Scroll-aware header ───────────────────────────────────
  var header = document.querySelector('.site-header');
  if (header) {
    var lastY = 0;
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      if (y > 60) {
        header.style.boxShadow = 'var(--shadow-sm)';
      } else {
        header.style.boxShadow = 'none';
      }
      lastY = y;
    }, { passive: true });
  }

})();
