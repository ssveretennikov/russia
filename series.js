/* Серия отчётов по регионам: пометки для автора, переключатель темы, просмотр фото. */

/* ---------- тема: светлая / тёмная (выбор запоминается) ---------- */
(function () {
  var btn = document.getElementById('themeBtn');
  if (!btn) return;
  var KEY = 'russia-theme', root = document.documentElement;
  var mq = window.matchMedia && matchMedia('(prefers-color-scheme: dark)');
  function current() { return root.dataset.theme || (mq && mq.matches ? 'dark' : 'light'); }
  function label() {
    var dark = current() === 'dark';
    btn.textContent = dark ? '☀' : '☾';
    var t = dark ? 'Включить светлую тему' : 'Включить тёмную тему';
    btn.setAttribute('aria-label', t); btn.title = t;
  }
  btn.hidden = false;
  btn.addEventListener('click', function () {
    var next = current() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
    label();
  });
  label();
})();

/* ---------- пометки для автора ---------- */
(function () {
  var notes = document.querySelectorAll('.note');
  var btn = document.getElementById('draftToggle');
  if (!btn || !notes.length) return;
  var KEY = 'russia-series-clean';
  var clean = false;
  try { clean = localStorage.getItem(KEY) === '1'; } catch (e) {}
  function render() {
    document.body.classList.toggle('clean', clean);
    btn.textContent = clean ? 'Показать пометки (' + notes.length + ')' : 'Скрыть пометки (' + notes.length + ')';
    btn.setAttribute('aria-pressed', clean ? 'true' : 'false');
  }
  btn.hidden = false;
  btn.addEventListener('click', function () {
    clean = !clean;
    try { localStorage.setItem(KEY, clean ? '1' : '0'); } catch (e) {}
    render();
  });
  render();
})();

/* ---------- просмотр фото: клик, стрелки, свайп, увеличение, Esc, «Назад» ---------- */
(function () {
  var imgs = [].slice.call(document.querySelectorAll('.ph img:not(.cover-bg)'));   // размытая подложка обложки — не кадр
  if (!imgs.length) return;
  var box = document.createElement('div');
  box.className = 'lb'; box.hidden = true;
  box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', 'Просмотр фото');
  box.innerHTML = '<button type="button" class="lb-x" aria-label="Закрыть">×</button>' +
    '<button type="button" class="lb-n lb-prev" aria-label="Предыдущее фото">‹</button>' +
    '<button type="button" class="lb-n lb-next" aria-label="Следующее фото">›</button>' +
    '<figure class="lb-f"><img alt="" draggable="false"><figcaption></figcaption></figure><div class="lb-c" aria-hidden="true"></div>' +
    '<div class="lb-live" aria-live="polite" aria-atomic="true"></div>';
  document.body.appendChild(box);
  var pic = box.querySelector('.lb-f img'), cap = box.querySelector('figcaption'), cnt = box.querySelector('.lb-c'),
      live = box.querySelector('.lb-live');
  var cur = -1, opener = null, inHistory = false;

  function caption(img) {
    var f = img.closest('figure'), c = f && f.querySelector('figcaption');
    if (!c) return img.alt || '';
    var t = c.querySelector('time'), rest = c.textContent.trim();
    return t ? t.textContent.trim() + ' · ' + rest.slice(t.textContent.length).trim() : rest;
  }

  /* увеличение: масштаб s и сдвиг tx, ty кадра относительно его места */
  var MAX = 4, s = 1, tx = 0, ty = 0;
  function apply() {
    pic.style.transform = s === 1 ? '' : 'translate(' + tx + 'px,' + ty + 'px) scale(' + s + ')';
    box.classList.toggle('lb-zoomed', s > 1);
  }
  function clampPan() {
    var w = pic.offsetWidth, h = pic.offsetHeight,
        mx = Math.max(0, (w * s - window.innerWidth) / 2, (w * s - w) / 2),
        my = Math.max(0, (h * s - window.innerHeight) / 2, (h * s - h) / 2);
    tx = Math.min(mx, Math.max(-mx, tx)); ty = Math.min(my, Math.max(-my, ty));
  }
  function zoomAt(ns, px, py) {                          // точка (px, py) экрана остаётся под пальцем
    ns = Math.min(MAX, Math.max(1, ns));
    var r = pic.getBoundingClientRect(), cx = r.left + r.width / 2 - tx, cy = r.top + r.height / 2 - ty;
    tx = px - cx - (px - cx - tx) * ns / s; ty = py - cy - (py - cy - ty) * ns / s;
    s = ns;
    if (s <= 1.01) { s = 1; tx = 0; ty = 0; }
    clampPan(); apply();
  }
  function resetZoom() { s = 1; tx = 0; ty = 0; apply(); }

  function show(i) {
    cur = (i + imgs.length) % imgs.length;
    var im = imgs[cur];
    resetZoom();
    pic.src = im.currentSrc || im.src; pic.alt = im.alt;
    cap.textContent = caption(im);
    cnt.textContent = (cur + 1) + ' / ' + imgs.length;
    live.textContent = (cur + 1) + ' из ' + imgs.length + (cap.textContent ? ' · ' + cap.textContent : '');
    [cur - 1, cur + 1].forEach(function (k) {            // соседние кадры подгружаем заранее
      var n = imgs[(k + imgs.length) % imgs.length]; if (n) new Image().src = n.currentSrc || n.src;
    });
  }
  function open(i, from) {
    opener = from || null; show(i); box.hidden = false;
    document.documentElement.classList.add('lb-open');
    try { history.pushState({ lb: 1 }, ''); inHistory = true; } catch (e) { inHistory = false; }   // «Назад» в телефоне закрывает просмотр
    box.querySelector('.lb-x').focus();
  }
  function hide() {
    box.hidden = true; pic.removeAttribute('src'); live.textContent = ''; resetZoom();
    document.documentElement.classList.remove('lb-open');
    if (opener) opener.focus({ preventScroll: true });
  }
  function close() {                                     // кнопка, Esc, фон: снимаем свою запись истории, иначе «Назад» сработает вхолостую
    if (box.hidden) return;
    hide();
    if (inHistory) { inHistory = false; history.back(); }
  }
  window.addEventListener('popstate', function () {
    if (box.hidden) return;
    inHistory = false; hide();
  });

  imgs.forEach(function (im, i) {
    im.classList.add('zoomable'); im.tabIndex = 0; im.setAttribute('role', 'button');
    im.setAttribute('aria-label', 'Открыть фото: ' + (im.alt || ''));
    im.addEventListener('click', function () { open(i, im); });
    im.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i, im); } });
  });
  box.querySelector('.lb-x').addEventListener('click', close);
  box.querySelector('.lb-prev').addEventListener('click', function () { show(cur - 1); });
  box.querySelector('.lb-next').addEventListener('click', function () { show(cur + 1); });
  var suppressClick = false;                             // после жеста клик по фону не закрывает окно
  box.addEventListener('click', function (e) {
    if (suppressClick) { suppressClick = false; return; }
    if (e.target === box || e.target.classList.contains('lb-f')) close();
  });
  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(cur - 1);
    else if (e.key === 'ArrowRight') show(cur + 1);
    else if (e.key === 'Tab') {                          // фокус остаётся внутри окна
      var f = [].slice.call(box.querySelectorAll('button')), a = document.activeElement, k = f.indexOf(a);
      e.preventDefault(); f[(k + (e.shiftKey ? -1 : 1) + f.length) % f.length].focus();
    }
  });

  /* касания: два пальца — увеличение, один — свайп (при масштабе 1) или сдвиг увеличенного кадра,
     двойное касание — увеличить в 2,5 раза или вернуть. Мышь эти жесты не трогают: на компьютере клики как раньше. */
  var pts = {}, n = 0, pinch = null, pan = null, start = null, lastTap = null;
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
  box.addEventListener('pointerdown', function (e) {
    if (e.pointerType === 'mouse' || e.target.closest('button')) return;
    pts[e.pointerId] = { x: e.clientX, y: e.clientY }; n++;
    if (n === 1) { start = { x: e.clientX, y: e.clientY, t: Date.now(), moved: false }; pan = { x: e.clientX, y: e.clientY, tx: tx, ty: ty }; }
    if (n === 2) {
      var p = Object.keys(pts).map(function (k) { return pts[k]; });
      pinch = { d: dist(p[0], p[1]), s: s }; start = null; pan = null;
    }
  });
  box.addEventListener('pointermove', function (e) {
    if (!pts[e.pointerId]) return;
    pts[e.pointerId] = { x: e.clientX, y: e.clientY };
    if (start && Math.hypot(e.clientX - start.x, e.clientY - start.y) > 10) start.moved = true;
    if (pinch && n >= 2) {
      var p = Object.keys(pts).map(function (k) { return pts[k]; });
      zoomAt(pinch.s * dist(p[0], p[1]) / pinch.d, (p[0].x + p[1].x) / 2, (p[0].y + p[1].y) / 2);
    } else if (pan && s > 1) {
      tx = pan.tx + e.clientX - pan.x; ty = pan.ty + e.clientY - pan.y; clampPan(); apply();
    }
  });
  function up(e) {
    if (!pts[e.pointerId]) return;
    delete pts[e.pointerId]; n = Math.max(0, n - 1);
    if (pinch) { suppressClick = true; if (n < 2) pinch = null; if (n === 1) { var k = Object.keys(pts)[0]; pan = { x: pts[k].x, y: pts[k].y, tx: tx, ty: ty }; } return; }
    if (!start || n) return;
    var dx = e.clientX - start.x, dy = e.clientY - start.y, now = Date.now();
    if (start.moved) {
      suppressClick = true;
      if (s === 1 && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(cur + (dx < 0 ? 1 : -1));
      lastTap = null;
    } else if (lastTap && now - lastTap.t < 300 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 30) {
      suppressClick = true; lastTap = null;
      if (s > 1) resetZoom(); else zoomAt(2.5, e.clientX, e.clientY);
    } else {
      lastTap = { x: e.clientX, y: e.clientY, t: now };
      if (s > 1) suppressClick = true;                   // одиночное касание увеличенного кадра не закрывает окно
    }
    start = null;
  }
  box.addEventListener('pointerup', up);
  box.addEventListener('pointercancel', up);
  box.addEventListener('touchmove', function (e) { e.preventDefault(); }, { passive: false });   // страница под окном не прокручивается
})();

/* Шапка-обложка: маршрут на телефоне прокручивается вбок. Край строки, за которым есть продолжение, уходит
   в прозрачность (классы scrolled / at-end); если строка длиннее экрана, её можно прокрутить и с клавиатуры. */
(function () {
  var r = document.querySelector('.under .route');
  if (!r) return;
  function sync() {
    var scrolls = r.scrollWidth > r.clientWidth + 1;
    if (scrolls) r.tabIndex = 0; else r.removeAttribute('tabindex');
    r.classList.toggle('scrolled', scrolls && r.scrollLeft > 2);
    r.classList.toggle('at-end', !scrolls || r.scrollLeft + r.clientWidth >= r.scrollWidth - 2);
  }
  r.addEventListener('scroll', sync, { passive: true });
  window.addEventListener('resize', sync);
  sync();
})();
