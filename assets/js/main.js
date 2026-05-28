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

  // ── Figure lightbox (click to enlarge) ────────────────────
  var figureImgs = document.querySelectorAll('.post-body figure img');
  if (figureImgs.length) {
    var overlay = null;

    function closeOverlay() {
      if (!overlay) return;
      overlay.classList.remove('is-open');
      // Allow CSS transition before removal
      setTimeout(function () {
        if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay);
        overlay = null;
      }, 180);
      document.body.style.overflow = '';
      document.removeEventListener('keydown', onKeydown);
    }

    function onKeydown(e) {
      if (e.key === 'Escape') closeOverlay();
    }

    function openOverlay(src, alt) {
      overlay = document.createElement('div');
      overlay.className = 'lightbox-overlay';
      overlay.setAttribute('role', 'dialog');
      overlay.setAttribute('aria-modal', 'true');
      overlay.setAttribute('aria-label', alt || 'Enlarged figure');
      var img = document.createElement('img');
      img.src = src;
      if (alt) img.alt = alt;
      overlay.appendChild(img);
      document.body.appendChild(overlay);
      document.body.style.overflow = 'hidden';
      // Force layout then add class to trigger fade-in
      void overlay.offsetWidth;
      overlay.classList.add('is-open');
      overlay.addEventListener('click', closeOverlay);
      document.addEventListener('keydown', onKeydown);
    }

    figureImgs.forEach(function (img) {
      img.classList.add('is-zoomable');
      img.addEventListener('click', function () {
        openOverlay(img.currentSrc || img.src, img.alt);
      });
    });
  }

})();
