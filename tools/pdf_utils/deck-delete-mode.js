<script>/* Delete mode — remove boxes, pills, rows and blocks you don't want.
   Press D to turn it on. Hover to target, click to remove.
   Alt+click removes the block around it. Ctrl+Z puts the last one back.
   Removals survive a reload, and Save bakes them into the file. */
(function () {
'use strict';

var CANDIDATES = [
  '.chip','.tag','.stamp','.num','.eyebrow','.said','.ans','.lab',
  'li','tr','.kv','.tier','.route','.act','.reg','.steps > div','.rail > div',
  '.phase > div','.gamegrid > div','.key > span','.rule','.chips','.arc',
  '.card','.persona','.mock','.pass','.game','.score','.was','.now',
  'p','h3','h4','table','.lockup','.lock','.note',
  '.g2 > div','.g3 > div','.g4 > div','.g5 > div','.split > div','.steps','.rail','.phase','.acts'
].join(',');

var NAMES = [
  ['.chip','pill'],['.tag','pill'],['.stamp','pill'],['tr','table row'],['li','list item'],
  ['.kv','line'],['.tier','level row'],['.route','row'],['.act','row'],['.reg','language card'],
  ['.card','box'],['.persona','person card'],['.mock','screen'],['.pass','pass card'],
  ['.game','illustration'],['.score','scoring box'],['.rule','divider'],['.arc','arc'],
  ['table','table'],['.lockup','logos'],['.lock','logos'],['h3','heading'],['h4','heading'],['p','text']
];

var STORE = (document.title || 'deck').replace(/[^a-z0-9]/gi,'-').toLowerCase() + '-deleted-v1';
var on = false, target = null, undoStack = [];

/* a structural path, stable for this file, so removals survive a reload */
function pathOf(el) {
  var parts = [], n = el;
  while (n && n !== document.body) {
    var p = n.parentElement; if (!p) break;
    parts.unshift(Array.prototype.indexOf.call(p.children, n));
    if (n.id) { parts.unshift(n.id); break; }
    n = p;
  }
  return parts.join('/');
}
function readList() { try { return JSON.parse(localStorage.getItem(STORE) || '[]'); } catch (e) { return []; } }
function writeList(l) { try { localStorage.setItem(STORE, JSON.stringify(l)); } catch (e) {} }

function nameFor(el) {
  for (var i = 0; i < NAMES.length; i++) if (el.matches(NAMES[i][0])) return NAMES[i][1];
  return 'block';
}

var style = document.createElement('style');
style.textContent =
  '.dm-on .canvas *{cursor:crosshair}' +
  '.dm-hit{outline:2px solid #E86C17!important;outline-offset:2px;' +
    'background:rgba(232,108,23,.12)!important;border-radius:4px}' +
  '#dm-tip{position:fixed;z-index:9999;pointer-events:none;background:#151515;color:#fff;' +
    'font:500 12px/1 Inter,system-ui,sans-serif;padding:6px 9px;border-radius:6px;white-space:nowrap;' +
    'box-shadow:0 4px 14px rgba(0,0,0,.35)}' +
  '#dm-bar{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);z-index:9999;' +
    'display:flex;align-items:center;gap:10px;background:#E86C17;color:#fff;border-radius:999px;' +
    'padding:9px 16px;font:500 13px/1 Inter,system-ui,sans-serif;box-shadow:0 6px 20px rgba(0,0,0,.3)}' +
  '#dm-bar button{background:rgba(255,255,255,.2);border:0;color:#fff;font:500 12px/1 inherit;' +
    'padding:6px 11px;border-radius:999px;cursor:pointer}' +
  '#dm-bar button:hover{background:rgba(255,255,255,.34)}' +
  '#dm-bar b{font-variant-numeric:tabular-nums}';
document.head.appendChild(style);

var tip = document.createElement('div'); tip.id = 'dm-tip'; tip.hidden = true;
var bar = document.createElement('div'); bar.id = 'dm-bar'; bar.hidden = true;
bar.innerHTML = '<span>Delete mode</span><b id="dm-count">0 removed</b>' +
  '<button id="dm-undo">Undo</button><button id="dm-all">Restore all</button>' +
  '<button id="dm-off">Done</button>';
document.addEventListener('DOMContentLoaded', add); add();
function add() { if (!document.body) return;
  if (!tip.parentNode) document.body.appendChild(tip);
  if (!bar.parentNode) document.body.appendChild(bar); }

function count() { return readList().length; }
function refresh() {
  var c = document.getElementById('dm-count');
  if (c) c.textContent = count() + (count() === 1 ? ' removed' : ' removed');
}

function pick(el, up) {
  if (!el || el.closest('#dm-bar') || el.closest('#bar')) return null;
  if (el.ownerSVGElement || el.tagName === 'svg') el = el.closest('.game') || el;
  var hit = el.closest(CANDIDATES);
  if (hit && up) { var p = hit.parentElement && hit.parentElement.closest(CANDIDATES); if (p) hit = p; }
  if (hit && (hit.closest('.foot') && hit.matches('.pageno'))) return null;
  return hit;
}

function mark(el) {
  if (target === el) return;
  if (target) target.classList.remove('dm-hit');
  target = el;
  if (target) { target.classList.add('dm-hit'); tip.hidden = false; }
  else tip.hidden = true;
}

function onMove(e) {
  if (!on) return;
  mark(pick(e.target, e.altKey));
  if (target) {
    tip.textContent = 'Remove this ' + nameFor(target) + (e.altKey ? '' : '  ·  alt for the block around it');
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 260) + 'px';
    tip.style.top = (e.clientY + 18) + 'px';
  }
}

function remove(el) {
  var rec = { path: pathOf(el), parent: el.parentElement, next: el.nextSibling, node: el };
  var list = readList(); list.push(rec.path); writeList(list);
  undoStack.push(rec);
  el.classList.remove('dm-hit');
  el.remove();
  target = null; tip.hidden = true;
  refresh();
}

function onClick(e) {
  if (!on) return;
  if (e.target.closest('#dm-bar')) return;
  e.preventDefault(); e.stopPropagation();
  var el = pick(e.target, e.altKey);
  if (el) remove(el);
}

function undo() {
  var rec = undoStack.pop(); if (!rec) return;
  if (rec.parent) rec.parent.insertBefore(rec.node, rec.next);
  var list = readList(); var i = list.lastIndexOf(rec.path); if (i > -1) list.splice(i, 1); writeList(list);
  refresh();
}

function restoreAll() {
  while (undoStack.length) undo();
  writeList([]); refresh();
  if (readList().length === 0 && document.querySelectorAll('[data-dm-gone]').length === 0) return;
  location.reload();
}

/* re-apply saved removals on load */
function applySaved() {
  var list = readList(); if (!list.length) return;
  var all = document.querySelectorAll('.canvas *');
  var byPath = {};
  Array.prototype.forEach.call(all, function (el) { byPath[pathOf(el)] = el; });
  list.forEach(function (p) { var el = byPath[p]; if (el) el.remove(); });
  refresh();
}

function toggle(force) {
  on = (force === undefined) ? !on : force;
  document.body.classList.toggle('dm-on', on);
  bar.hidden = !on; if (!on) { mark(null); tip.hidden = true; }
  refresh();
}
window.__toggleDeleteMode = toggle;

document.addEventListener('mousemove', onMove, true);
document.addEventListener('click', onClick, true);
document.addEventListener('keydown', function (e) {
  if (e.target.closest('[contenteditable="true"],input,textarea')) return;
  if ((e.key === 'd' || e.key === 'D') && !e.ctrlKey && !e.metaKey) {
    if (document.body.classList.contains('edit-mode')) return;
    e.preventDefault(); toggle();
  } else if (on && e.key === 'Escape') { e.preventDefault(); toggle(false); }
  else if (on && (e.ctrlKey || e.metaKey) && e.key === 'z') { e.preventDefault(); undo(); }
}, true);

bar.addEventListener('click', function (e) {
  var id = e.target.id;
  if (id === 'dm-undo') undo();
  else if (id === 'dm-all') restoreAll();
  else if (id === 'dm-off') toggle(false);
});

/* Save should bake the removals in, then forget them */
var origSave = null;
setTimeout(function () {
  origSave = window.saveToFile;
  if (typeof origSave !== 'function') return;
  window.saveToFile = function () {
    toggle(false);
    var r = origSave.apply(this, arguments);
    writeList([]); undoStack = [];
    return r;
  };
}, 0);

applySaved();
})();
</script>
