/* Главная: карта, фильтры, карточка региона. Данные берутся из списка регионов на странице (li[data-code]). */
(function () {
  var svg = document.querySelector('.rumap');
  if (!svg) return;
  var card = document.getElementById('mcard');
  var hint = card.innerHTML;
  var paths = [].slice.call(svg.querySelectorAll('path'));
  var items = [].slice.call(document.querySelectorAll('li.reg[data-code]'));
  var secs = [].slice.call(document.querySelectorAll('section.fo'));
  var byCode = {};
  items.forEach(function (li) { byCode[li.dataset.code] = li; });
  var state = { fo: '', year: '' };
  var picked = null;
  var TR = { car: { icon: '🚗', text: 'на машине' }, bus: { icon: '🚌', text: 'на автобусе' },
             plane: { icon: '✈️', text: 'на самолёте' }, train: { icon: '🚆', text: 'на поезде' } };

  function linkOf(code) {
    var li = byCode[code], a = li && li.querySelector('a.code');
    return a ? a.getAttribute('href') : null;
  }
  function show(code) {
    var li = byCode[code];
    if (!li) { card.innerHTML = hint; return; }
    var href = linkOf(code);
    var name = li.querySelector('.nm, a:not(.code)');
    var sub = li.querySelector('small');
    var local = li.classList.contains('new');
    var cap = sub ? sub.textContent.replace(/впереди/, '').trim() : '';
    var date = li.dataset.date ? 'Первый визит: ' + li.dataset.date : '';
    var tr = TR[li.dataset.tr];
    if (tr) date += ' · ' + tr.icon + ' ' + tr.text;
    card.innerHTML = '';
    var b = document.createElement('span'); b.className = 'code'; b.textContent = code;
    var t = document.createElement('div'); t.className = 'mt';
    var n = document.createElement('strong'); n.textContent = name ? name.textContent : code;
    var s = document.createElement('small'); s.textContent = [cap, date].filter(Boolean).join(' · ');
    t.appendChild(n); t.appendChild(s);
    card.appendChild(b); card.appendChild(t);
    if (href) {
      var a = document.createElement('a'); a.className = 'go'; a.href = href;
      a.textContent = local ? 'Открыть отчёт →' : 'Отчёт во ВКонтакте →';
      card.appendChild(a);
    }
  }
  function mark(code) {
    paths.forEach(function (p) { p.classList.toggle('on', p.dataset.code === code); });
  }
  function go(code) {
    var href = linkOf(code);
    if (href) location.href = href;
  }

  paths.forEach(function (p) {
    var code = p.dataset.code;
    p.addEventListener('pointerenter', function (ev) { if (ev.pointerType === 'mouse' && !picked) { show(code); mark(code); } });
    p.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse' && !picked) { card.innerHTML = hint; mark(''); } });
    p.addEventListener('focus', function () { show(code); mark(code); });
    p.addEventListener('click', function (ev) {
      if (ev.pointerType === 'touch' || ev.pointerType === 'pen') { picked = code; show(code); mark(code); return; }
      go(code);
    });
    p.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); go(code); } });
  });
  document.addEventListener('click', function (ev) {
    if (picked && !ev.target.closest('.rumap, .mcard')) { picked = null; card.innerHTML = hint; mark(''); }
  });

  // фильтры
  function apply() {
    function ok(el) {
      return (!state.fo || el.dataset.fo === state.fo) && (!state.year || el.dataset.year === state.year);
    }
    paths.forEach(function (p) { p.classList.toggle('dim', !ok(p)); });
    items.forEach(function (li) { li.hidden = !ok(li); });
    secs.forEach(function (s) { s.hidden = !s.querySelector('li.reg:not([hidden])'); });
  }
  [].forEach.call(document.querySelectorAll('.chip'), function (c) {
    c.addEventListener('click', function () {
      state[c.dataset.k] = c.dataset.v;
      [].forEach.call(document.querySelectorAll('.chip[data-k="' + c.dataset.k + '"]'), function (x) {
        x.setAttribute('aria-pressed', x === c ? 'true' : 'false');
      });
      apply();
    });
  });

  // анимация: регионы загораются по датам первого визита
  var playBtn = document.getElementById('play'), adate = document.getElementById('adate');
  var seq = items.filter(function (li) { return li.dataset.n !== undefined; })
    .sort(function (a, b) { return a.dataset.n - b.dataset.n; });
  var pathBy = {};
  paths.forEach(function (p) { pathBy[p.dataset.code] = p; });
  var timer = null, pos = 0, STEP = 380;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  function lit(n) {                     // показать первые n регионов
    var codes = {};
    for (var i = 0; i < n; i++) codes[seq[i].dataset.code] = 1;
    paths.forEach(function (p) {
      p.classList.toggle('off', !codes[p.dataset.code]);
      p.classList.remove('now');
    });
    if (n) {
      var cur = seq[n - 1];
      pathBy[cur.dataset.code].classList.add('now');
      show(cur.dataset.code);
      adate.textContent = cur.dataset.date;
    }
  }
  function stop(done) {
    clearInterval(timer); timer = null;
    playBtn.textContent = done ? '↺ Ещё раз' : '▶ Продолжить';
    if (done) playBtn.dataset.done = '1';
  }
  function reset() {
    paths.forEach(function (p) { p.classList.remove('off', 'now'); });
    card.innerHTML = hint; adate.textContent = '';
    delete playBtn.dataset.done; playBtn.textContent = '▶ Показать путь'; pos = 0;
  }
  function tick() {
    pos++; lit(pos);
    if (pos >= seq.length) { stop(true); }
  }
  playBtn.addEventListener('click', function () {
    if (timer) { stop(false); return; }                          // пауза
    if (playBtn.dataset.done) { delete playBtn.dataset.done; pos = 0; }
    if (pos === 0) {                                             // фильтры на время показа сбрасываем
      state.fo = ''; state.year = ''; apply();
      [].forEach.call(document.querySelectorAll('.chip'), function (x) { x.setAttribute('aria-pressed', x.dataset.v === '' ? 'true' : 'false'); });
    }
    picked = null;
    playBtn.textContent = '⏸ Пауза';
    if (still) { pos = seq.length; lit(pos); stop(true); return; }   // без движения: сразу итог
    tick();
    timer = setInterval(tick, STEP);
  });
  // выбор фильтра во время показа останавливает его
  [].forEach.call(document.querySelectorAll('.chip'), function (c) {
    c.addEventListener('click', function () { if (timer || pos) { clearInterval(timer); timer = null; reset(); } });
  });
})();
