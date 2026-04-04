/* AAA / CAA Process Wiki -- wiki.js */
(function () {
  'use strict';

  /* ── Sidebar collapse ─────────────────────────────────────────────── */
  var sidebar       = document.getElementById('sidebar');
  var sidebarToggle = document.getElementById('sidebarToggle');
  var topbarToggle  = document.getElementById('topbarToggle');

  function collapseState() {
    try { return localStorage.getItem('sidebarCollapsed') === '1'; } catch(e) { return false; }
  }
  function setCollapseState(v) {
    try { localStorage.setItem('sidebarCollapsed', v ? '1' : '0'); } catch(e) {}
  }

  if (sidebar) {
    if (collapseState()) sidebar.classList.add('collapsed');

    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', function () {
        var c = sidebar.classList.toggle('collapsed');
        setCollapseState(c);
      });
    }
    if (topbarToggle) {
      topbarToggle.addEventListener('click', function () {
        sidebar.classList.toggle('mobile-open');
      });
    }

    /* L1 accordion */
    sidebar.querySelectorAll('.nav-l1').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (sidebar.classList.contains('collapsed')) return;
        var domain = el.closest('.nav-domain');
        if (!domain) return;
        var href = el.getAttribute('href');
        var isOpen = domain.classList.contains('open');
        /* Close all other domains */
        sidebar.querySelectorAll('.nav-domain.open').forEach(function (d) {
          if (d !== domain) d.classList.remove('open');
        });
        /* If already open and has a nav target: navigate without toggling closed */
        if (isOpen && href && href !== '#') {
          e.preventDefault();
          window.location.href = href;
          return;
        }
        /* Otherwise toggle open/closed */
        domain.classList.toggle('open');
        e.preventDefault();
        if (href && href !== '#') setTimeout(function(){ window.location.href = href; }, 120);
      });
    });

    /* L2 accordion */
    sidebar.querySelectorAll('.nav-l2-title').forEach(function (el) {
      el.addEventListener('click', function (e) {
        var group = el.closest('.nav-l2-group');
        if (!group) return;
        group.classList.toggle('open');
        e.preventDefault();
        var href = el.getAttribute('href');
        if (href && href !== '#') setTimeout(function(){ window.location.href = href; }, 120);
      });
    });
  }

  /* ── Lightbox with zoom + pan ─────────────────────────────────────── */
  var overlay = document.getElementById('lightbox');
  var lbImg   = document.getElementById('lightboxImg');

  if (!overlay || !lbImg) return;

  /* State */
  var scale    = 1;
  var originX  = 0;
  var originY  = 0;
  var startX   = 0;
  var startY   = 0;
  var dragging = false;
  var lastDist = 0;          /* for pinch-zoom */

  var MIN_SCALE = 0.5;
  var MAX_SCALE = 8;
  var ZOOM_STEP = 0.25;

  /* ── Controls bar ── */
  var controls = document.createElement('div');
  controls.id  = 'lbControls';
  controls.innerHTML =
    '<button id="lbZoomIn"  title="Zoom in">&#xFF0B;</button>' +
    '<button id="lbZoomOut" title="Zoom out">&#x2212;</button>' +
    '<button id="lbReset"   title="Reset">&#x21BA;</button>' +
    '<span   id="lbScale">100%</span>' +
    '<button id="lbClose"   title="Close (Esc)">&#x2715;</button>';
  overlay.appendChild(controls);

  function updateTransform() {
    lbImg.style.transform =
      'translate(' + originX + 'px,' + originY + 'px) scale(' + scale + ')';
    document.getElementById('lbScale').textContent =
      Math.round(scale * 100) + '%';
  }

  function resetView() {
    scale   = 1;
    originX = 0;
    originY = 0;
    updateTransform();
  }

  function zoomBy(delta, cx, cy) {
    /* cx, cy = zoom focal point in viewport coords; default = centre */
    if (cx === undefined) {
      cx = overlay.clientWidth  / 2;
      cy = overlay.clientHeight / 2;
    }
    var next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale + delta));
    if (next === scale) return;
    /* Adjust origin so the focal point stays fixed */
    var ratio  = next / scale;
    var imgX   = cx - overlay.getBoundingClientRect().left;
    var imgY   = cy - overlay.getBoundingClientRect().top;
    originX    = imgX - ratio * (imgX - originX);
    originY    = imgY - ratio * (imgY - originY);
    scale      = next;
    updateTransform();
  }

  /* Open */
  function openLightbox(src, title) {
    lbImg.src = src;
    lbImg.alt = title || '';
    resetView();
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  /* Close */
  function closeLightbox() {
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    /* Small delay so closing animation runs before clearing src */
    setTimeout(function(){ lbImg.src = ''; }, 200);
  }

  /* Wire up trigger links */
  document.querySelectorAll('a[data-lightbox]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      openLightbox(a.href, a.dataset.title || '');
    });
  });

  /* Control buttons */
  document.getElementById('lbZoomIn') .addEventListener('click', function(e){ e.stopPropagation(); zoomBy(+ZOOM_STEP); });
  document.getElementById('lbZoomOut').addEventListener('click', function(e){ e.stopPropagation(); zoomBy(-ZOOM_STEP); });
  document.getElementById('lbReset')  .addEventListener('click', function(e){ e.stopPropagation(); resetView(); });
  document.getElementById('lbClose')  .addEventListener('click', function(e){ e.stopPropagation(); closeLightbox(); });

  /* Click backdrop (not image / controls) to close */
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) closeLightbox();
  });

  /* Escape key */
  document.addEventListener('keydown', function (e) {
    if (!overlay.classList.contains('active')) return;
    if (e.key === 'Escape')               { closeLightbox(); }
    if (e.key === '+' || e.key === '=')   { zoomBy(+ZOOM_STEP); }
    if (e.key === '-')                    { zoomBy(-ZOOM_STEP); }
    if (e.key === '0')                    { resetView(); }
  });

  /* Mouse wheel zoom */
  overlay.addEventListener('wheel', function (e) {
    e.preventDefault();
    var delta = e.deltaY < 0 ? +ZOOM_STEP : -ZOOM_STEP;
    zoomBy(delta, e.clientX, e.clientY);
  }, { passive: false });

  /* Mouse drag pan */
  lbImg.addEventListener('mousedown', function (e) {
    if (e.button !== 0) return;
    dragging = true;
    startX   = e.clientX - originX;
    startY   = e.clientY - originY;
    lbImg.style.cursor = 'grabbing';
    e.preventDefault();
  });
  document.addEventListener('mousemove', function (e) {
    if (!dragging) return;
    originX = e.clientX - startX;
    originY = e.clientY - startY;
    updateTransform();
  });
  document.addEventListener('mouseup', function () {
    dragging = false;
    lbImg.style.cursor = scale > 1 ? 'grab' : 'zoom-in';
  });

  /* Touch: single-finger drag, two-finger pinch-zoom */
  lbImg.addEventListener('touchstart', function (e) {
    if (e.touches.length === 1) {
      dragging = true;
      startX   = e.touches[0].clientX - originX;
      startY   = e.touches[0].clientY - originY;
    } else if (e.touches.length === 2) {
      dragging = false;
      lastDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY);
    }
    e.preventDefault();
  }, { passive: false });

  lbImg.addEventListener('touchmove', function (e) {
    if (e.touches.length === 1 && dragging) {
      originX = e.touches[0].clientX - startX;
      originY = e.touches[0].clientY - startY;
      updateTransform();
    } else if (e.touches.length === 2) {
      var dist  = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY);
      var cx    = (e.touches[0].clientX + e.touches[1].clientX) / 2;
      var cy    = (e.touches[0].clientY + e.touches[1].clientY) / 2;
      var delta = (dist - lastDist) / 200;
      zoomBy(delta, cx, cy);
      lastDist = dist;
    }
    e.preventDefault();
  }, { passive: false });

  lbImg.addEventListener('touchend', function () {
    dragging = false;
    lastDist = 0;
  });

  /* Double-click: zoom in steps; at MAX reset */
  lbImg.addEventListener('dblclick', function (e) {
    if (scale >= MAX_SCALE * 0.9) { resetView(); }
    else { zoomBy(+ZOOM_STEP * 3, e.clientX, e.clientY); }
    e.preventDefault();
  });

  /* ── SEARCH — inject box + redirect to search.html on Enter ── */
  (function() {

    /* Resolve site root robustly for multi-depth pages */
    function getSiteRoot() {
      var parts = window.location.pathname.split('/');
      var repoIdx = parts.indexOf('AAAProcessWiki');
      if (repoIdx >= 0) return parts.slice(0, repoIdx + 1).join('/') + '/';
      /* Fallback: walk up from depth using known page depths */
      /* Process pages: l1_slug/l2_slug/pid.html  → ../../  */
      /* L1 index:      l1_slug/index.html         → ../     */
      /* EA page:       ea/ea-01.html              → ../     */
      /* Home:          index.html                 → ./      */
      var depth = parts.filter(function(p){ return p !== ''; }).length - 1;
      /* subtract 1 because last segment is the file */
      var prefix = '';
      for (var i = 0; i < depth; i++) prefix += '../';
      return prefix || './';
    }

    function getSearchUrl(q) {
      return getSiteRoot() + 'search.html?q=' + encodeURIComponent(q.trim());
    }

    /* Inject search box into topbar if not already present */
    var topbar   = document.querySelector('.topbar');
    var existing = document.getElementById('searchBox');
    if (topbar && !existing) {
      var inp = document.createElement('input');
      inp.type        = 'text';
      inp.id          = 'searchBox';
      inp.className   = 'topbar-search';
      inp.placeholder = 'Search processes\u2026 (/)';
      inp.autocomplete = 'off';
      topbar.appendChild(inp);
    }

    var searchBox = document.getElementById('searchBox');
    if (!searchBox) return;

    searchBox.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && searchBox.value.trim()) {
        window.location.href = getSearchUrl(searchBox.value);
      }
      if (e.key === 'Escape') { searchBox.value = ''; searchBox.blur(); }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === '/' && document.activeElement !== searchBox) {
        e.preventDefault(); searchBox.focus(); searchBox.select();
      }
    });
  })();

})();
