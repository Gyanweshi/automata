/* ─────────────────────────────────────────────────────────────────────────
   INLINE EDITOR — generic slide presentation editor
   Version: 1.0

   How it works:
   • Press E to enter / exit edit mode
   • Click any element with class="editable" to edit text inline
   • Drag the ⤡ handle (bottom-right corner) to resize width + height
   • Drag the purple bar between elements to adjust spacing independently
   • Ctrl+S  or the 💾 button downloads the file with all edits baked in
   • Changes survive page reload via localStorage (keyed to page title)

   Required conventions in the HTML template:
   • Each slide → <section class="slide">
   • Content column → <div class="slide-content"> (flex-direction:column)
   • Every editable block → add class="editable"

   The editor is self-contained — drop the script tag anywhere before </body>.
   ───────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  /* ── storage key (one per presentation title) ──────────────────────── */
  var STORE = (document.title || 'slide')
    .replace(/[^a-z0-9]/gi, '-').toLowerCase() + '-ie-v1';

  /* ── tracked CSS properties ─────────────────────────────────────────── */
  var PROPS = [
    'width', 'height', 'position', 'align-self', 'justify-self',
    'max-width', 'overflow', 'margin-bottom', 'row-gap'
  ];

  /* ── helpers ─────────────────────────────────────────────────────────── */
  function imp(el, prop, val) { el.style.setProperty(prop, val, 'important'); }
  function gv(el, prop)       { return el.style.getPropertyValue(prop); }

  /* ── persistence ─────────────────────────────────────────────────────── */
  function saveAll() {
    var data = {};
    function snap(el, key) {
      var d = {};
      PROPS.forEach(function (p) { var v = gv(el, p); if (v) d[p] = v; });
      if (Object.keys(d).length) data[key] = d;
    }
    document.querySelectorAll('[data-ie-id]').forEach(function (el) {
      snap(el, 'i:' + el.dataset.ieId);
    });
    document.querySelectorAll('[data-ie-child-id]').forEach(function (el) {
      snap(el, 'c:' + el.dataset.ieChildId);
    });
    document.querySelectorAll('[data-ie-gap-id]').forEach(function (el) {
      snap(el, 'g:' + el.dataset.ieGapId);
    });
    try { localStorage.setItem(STORE, JSON.stringify(data)); } catch (e) {}
  }

  function restoreAll() {
    var data;
    try { data = JSON.parse(localStorage.getItem(STORE) || 'null'); } catch (e) {}
    if (!data) return;
    function apply(el, key) {
      var d = data[key]; if (!d) return;
      Object.keys(d).forEach(function (p) { imp(el, p, d[p]); });
    }
    document.querySelectorAll('[data-ie-id]').forEach(function (el) {
      apply(el, 'i:' + el.dataset.ieId);
    });
    document.querySelectorAll('[data-ie-child-id]').forEach(function (el) {
      apply(el, 'c:' + el.dataset.ieChildId);
    });
    document.querySelectorAll('[data-ie-gap-id]').forEach(function (el) {
      apply(el, 'g:' + el.dataset.ieGapId);
    });
  }

  /* ── inject UI chrome styles ─────────────────────────────────────────── */
  var uiStyle = document.createElement('style');
  uiStyle.textContent = [
    /* EDITING badge */
    '#ie-badge{position:fixed;top:16px;left:50%;transform:translateX(-50%);',
    'background:#4815D8;color:#fff;font-family:Inter,system-ui,sans-serif;',
    'font-size:13px;font-weight:700;letter-spacing:0.08em;padding:7px 22px;',
    'border-radius:100px;z-index:99999;display:none;pointer-events:none;',
    'box-shadow:0 4px 16px rgba(72,21,216,0.35);}',
    '#ie-badge::after{content:" · E to exit";font-weight:400;opacity:0.75;}',
    'body.edit-mode #ie-badge{display:block;}',
    /* contenteditable outlines */
    'body.edit-mode [contenteditable]{outline:2px dashed rgba(72,21,216,0.4);',
    'outline-offset:3px;cursor:text;border-radius:3px;}',
    'body.edit-mode [contenteditable]:focus{outline:2px solid #4815D8;',
    'background:rgba(72,21,216,0.03);}',
    /* resize handle ⤡ */
    '.ie-rh{position:absolute!important;bottom:2px!important;right:2px!important;',
    'width:22px;height:22px;background:#4815D8;border-radius:4px 0 4px 0;',
    'cursor:nwse-resize;z-index:9999;display:flex;align-items:center;',
    'justify-content:center;font-size:12px;color:#fff;user-select:none;',
    'box-shadow:0 2px 8px rgba(72,21,216,0.4);}',
    /* dashed element outline in edit mode */
    '.ie-el-outline{outline:2px dashed rgba(72,21,216,0.28)!important;',
    'outline-offset:3px!important;}',
    /* gap drag bars */
    '.ie-gap{display:flex!important;align-items:center;justify-content:center;',
    'min-height:18px;cursor:ns-resize;user-select:none;position:relative;',
    'z-index:8000;flex-shrink:0;width:100%;}',
    '.ie-gap::before{content:"";position:absolute;left:0;right:0;top:50%;',
    'height:2px;background:rgba(72,21,216,0.15);}',
    '.ie-gap span{background:#fff;padding:2px 10px;position:relative;',
    'border:1px dashed rgba(72,21,216,0.35);border-radius:4px;',
    'font-size:10px;color:rgba(72,21,216,0.65);font-family:Inter,system-ui,sans-serif;}',
    /* 💾 save button */
    '#ie-save-btn{position:fixed;bottom:24px;right:24px;',
    'background:#4815D8;color:#fff;border:none;padding:10px 20px;',
    'border-radius:10px;cursor:pointer;font-family:Inter,system-ui,sans-serif;',
    'font-weight:700;font-size:14px;z-index:99999;display:none;',
    'box-shadow:0 4px 20px rgba(72,21,216,0.45);letter-spacing:0.02em;}',
    'body.edit-mode #ie-save-btn{display:block;}',
    '#ie-save-btn:hover{background:#3610b0;}',
  ].join('');
  document.head.appendChild(uiStyle);

  var badge = document.createElement('div');
  badge.id = 'ie-badge';
  badge.textContent = 'EDITING';
  document.body.appendChild(badge);

  /* ── selectors ───────────────────────────────────────────────────────── */
  // Any element with class="editable" gets a resize handle AND is text-editable.
  // Add that class to every content block in your slide templates.
  var EDITABLE_SEL = '.editable';
  var RESIZE_SEL   = '.editable';

  /* ── stamp stable data-ie-* IDs before edit mode ever runs ──────────── */
  function assignIds() {
    document.querySelectorAll('.slide').forEach(function (slide, si) {
      /* resize IDs */
      slide.querySelectorAll(RESIZE_SEL).forEach(function (el, ei) {
        if (!el.dataset.ieId) el.dataset.ieId = 'r' + si + 'e' + ei;
      });
      /* gap-bar IDs: .slide-content containers and their direct children */
      slide.querySelectorAll('.slide-content').forEach(function (sc, sci) {
        if (!sc.dataset.ieGapId) sc.dataset.ieGapId = 'g' + si + 's' + sci;
        Array.from(sc.children).forEach(function (child, ci) {
          if (!child.dataset.ieChildId)
            child.dataset.ieChildId = 'k' + si + 's' + sci + 'i' + ci;
        });
      });
    });
  }

  /* ── resize handle ───────────────────────────────────────────────────── */
  function attachResize(el) {
    if (el.dataset.ieHandled) return;
    el.dataset.ieHandled = '1';
    if (!el.dataset.ieId) return;

    el.classList.add('ie-el-outline');
    imp(el, 'position',    'relative');
    imp(el, 'align-self',  'flex-start');
    imp(el, 'justify-self','start');
    imp(el, 'max-width',   'none');
    imp(el, 'overflow',    'auto');
    if (!gv(el, 'width'))  imp(el, 'width',  el.offsetWidth  + 'px');
    if (!gv(el, 'height')) imp(el, 'height', el.offsetHeight + 'px');

    var h = document.createElement('div');
    h.className = 'ie-rh';
    h.textContent = '⤡';
    h.title = 'Drag to resize';
    el.appendChild(h);

    h.addEventListener('mousedown', function (e) {
      e.preventDefault(); e.stopPropagation();
      var sx = e.clientX, sy = e.clientY, sw = el.offsetWidth, sh = el.offsetHeight;
      function mv(ev) {
        var nw = sw + (ev.clientX - sx), nh = sh + (ev.clientY - sy);
        if (nw > 40) imp(el, 'width',  nw + 'px');
        if (nh > 20) imp(el, 'height', nh + 'px');
      }
      function up() {
        document.removeEventListener('mousemove', mv);
        document.removeEventListener('mouseup',   up);
        saveAll();
      }
      document.addEventListener('mousemove', mv);
      document.addEventListener('mouseup',   up);
    });

    cleanups.push(function () {
      el.classList.remove('ie-el-outline');
      delete el.dataset.ieHandled;
      if (h.parentNode) h.parentNode.removeChild(h);
    });
  }

  /* ── gap bars between flex children ─────────────────────────────────── */
  function attachGapBars(container) {
    var children = Array.from(container.children).filter(function (c) {
      return c.dataset.ieChildId;
    });
    if (children.length < 2) return;

    /* first time: collapse CSS gap, seed per-child margin-bottom */
    if (!gv(container, 'row-gap')) {
      var cs = getComputedStyle(container);
      var initGap = parseFloat(cs.rowGap) || parseFloat(cs.gap) || 24;
      imp(container, 'row-gap', '0px');
      children.forEach(function (child, i) {
        if (i < children.length - 1 && !gv(child, 'margin-bottom'))
          imp(child, 'margin-bottom', initGap + 'px');
      });
    }

    var inserted = [];
    children.forEach(function (child, i) {
      if (i >= children.length - 1) return;
      var cur = parseFloat(gv(child, 'margin-bottom')) || 0;

      var bar = document.createElement('div');
      bar.className = 'ie-gap';
      var lbl = document.createElement('span');
      lbl.textContent = Math.round(cur) + 'px gap';
      bar.appendChild(lbl);
      child.after(bar);
      inserted.push(bar);

      bar.addEventListener('mousedown', function (e) {
        e.preventDefault(); e.stopPropagation();
        var sy = e.clientY, sg = parseFloat(gv(child, 'margin-bottom')) || cur;
        function mv(ev) {
          var ng = Math.max(0, sg + (ev.clientY - sy));
          imp(child, 'margin-bottom', ng + 'px');
          lbl.textContent = Math.round(ng) + 'px gap';
        }
        function up() {
          document.removeEventListener('mousemove', mv);
          document.removeEventListener('mouseup',   up);
          saveAll();
        }
        document.addEventListener('mousemove', mv);
        document.addEventListener('mouseup',   up);
      });
    });

    cleanups.push(function () {
      inserted.forEach(function (b) { if (b.parentNode) b.parentNode.removeChild(b); });
    });
  }

  /* ── enter / exit edit mode ──────────────────────────────────────────── */
  var editing = false, cleanups = [];
  function stopNav(e) { e.stopPropagation(); }

  function enterEdit() {
    editing = true; cleanups = [];
    document.body.classList.add('edit-mode');
    document.querySelectorAll(EDITABLE_SEL).forEach(function (el) {
      el.setAttribute('contenteditable', 'true');
      el.addEventListener('keydown', stopNav, true);
      cleanups.push(function () {
        el.removeAttribute('contenteditable');
        el.removeEventListener('keydown', stopNav, true);
      });
    });
    document.querySelectorAll(RESIZE_SEL).forEach(attachResize);
    document.querySelectorAll('.slide-content').forEach(attachGapBars);
  }

  function exitEdit() {
    editing = false;
    document.body.classList.remove('edit-mode');
    cleanups.forEach(function (fn) { fn(); });
    cleanups = [];
    saveAll();
  }

  window.__toggleEditMode = function () { editing ? exitEdit() : enterEdit(); };

  /* ── save to file ────────────────────────────────────────────────────── */
  // Clones the live DOM, strips editor chrome, triggers a browser download.
  // The downloaded file replaces this one as the working copy — all edits
  // are baked into inline styles and text content, no server needed.
  function saveToFile() {
    if (editing) exitEdit();
    var clone = document.documentElement.cloneNode(true);
    clone.querySelectorAll('.ie-rh,.ie-gap,#ie-badge,#ie-save-btn').forEach(function (n) {
      n.parentNode.removeChild(n);
    });
    clone.querySelectorAll('[data-ie-handled],[contenteditable]').forEach(function (n) {
      n.removeAttribute('data-ie-handled');
      n.removeAttribute('contenteditable');
    });
    if (clone.body) clone.body.classList.remove('edit-mode');
    var fname = (document.title || 'presentation')
      .replace(/[^a-z0-9_\-]/gi, '_') + '.html';
    var html = '<!DOCTYPE html>\n' + clone.outerHTML;
    var blob = new Blob([html], { type: 'text/html' });
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href = url; a.download = fname; a.click();
    URL.revokeObjectURL(url);
  }
  window.saveToFile = saveToFile;

  /* ── keyboard shortcuts ──────────────────────────────────────────────── */
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault(); saveToFile(); return;
    }
    if (e.target.getAttribute && e.target.getAttribute('contenteditable') === 'true') return;
    if (e.key === 'e' || e.key === 'E') window.__toggleEditMode();
  });

  /* ── 💾 save button (visible only in edit mode) ─────────────────────── */
  var saveBtn = document.createElement('button');
  saveBtn.id = 'ie-save-btn';
  saveBtn.textContent = '💾 Save file';
  saveBtn.title = 'Bake all edits into the HTML file (Ctrl+S)';
  saveBtn.onclick = saveToFile;
  document.body.appendChild(saveBtn);

  /* ── boot ────────────────────────────────────────────────────────────── */
  assignIds();   // stamp data-ie-* attributes on all matching elements
  restoreAll();  // re-apply any localStorage backup from previous sessions
})();
