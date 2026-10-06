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

/* ---------- просмотр фото: клик, стрелки, свайп, Esc ---------- */
(function () {
  var imgs = [].slice.call(document.querySelectorAll('.ph img:not(.cover-bg)'));   // размытая подложка обложки — не кадр
  if (!imgs.length) return;
  var box = document.createElement('div');
  box.className = 'lb'; box.hidden = true;
  box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', 'Просмотр фото');
  box.innerHTML = '<button type="button" class="lb-x" aria-label="Закрыть">×</button>' +
    '<button type="button" class="lb-n lb-prev" aria-label="Предыдущее фото">‹</button>' +
    '<button type="button" class="lb-n lb-next" aria-label="Следующее фото">›</button>' +
    '<figure class="lb-f"><img alt=""><figcaption></figcaption></figure><div class="lb-c"></div>';
  document.body.appendChild(box);
  var pic = box.querySelector('.lb-f img'), cap = box.querySelector('figcaption'), cnt = box.querySelector('.lb-c');
  var cur = -1, opener = null;

  function caption(img) {
    var f = img.closest('figure'), c = f && f.querySelector('figcaption');
    if (!c) return img.alt || '';
    var t = c.querySelector('time'), rest = c.textContent.trim();
    return t ? t.textContent.trim() + ' · ' + rest.slice(t.textContent.length).trim() : rest;
  }
  function show(i) {
    cur = (i + imgs.length) % imgs.length;
    var im = imgs[cur];
    pic.src = im.currentSrc || im.src; pic.alt = im.alt;
    cap.textContent = caption(im);
    cnt.textContent = (cur + 1) + ' / ' + imgs.length;
    [cur - 1, cur + 1].forEach(function (k) {            // соседние кадры подгружаем заранее
      var n = imgs[(k + imgs.length) % imgs.length]; if (n) new Image().src = n.currentSrc || n.src;
    });
  }
  function open(i, from) {
    opener = from || null; show(i); box.hidden = false;
    document.documentElement.classList.add('lb-open');
    box.querySelector('.lb-x').focus();
  }
  function close() {
    box.hidden = true; pic.removeAttribute('src');
    document.documentElement.classList.remove('lb-open');
    if (opener) opener.focus();
  }
  imgs.forEach(function (im, i) {
    im.classList.add('zoomable'); im.tabIndex = 0; im.setAttribute('role', 'button');
    im.setAttribute('aria-label', 'Открыть фото: ' + (im.alt || ''));
    im.addEventListener('click', function () { open(i, im); });
    im.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i, im); } });
  });
  box.querySelector('.lb-x').addEventListener('click', close);
  box.querySelector('.lb-prev').addEventListener('click', function () { show(cur - 1); });
  box.querySelector('.lb-next').addEventListener('click', function () { show(cur + 1); });
  box.addEventListener('click', function (e) { if (e.target === box || e.target.classList.contains('lb-f')) close(); });
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
  var x0 = null, y0 = 0;
  box.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
  box.addEventListener('touchend', function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(cur + (dx < 0 ? 1 : -1));
  }, { passive: true });
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
