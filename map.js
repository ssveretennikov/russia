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
    // в <small> столица текстом и ссылки на части отчёта; в подпись карточки идёт только текст
    var cap = sub ? [].filter.call(sub.childNodes, function (x) { return x.nodeType === 3; })
      .map(function (x) { return x.textContent; }).join(' ').replace(/·|впереди/g, ' ').replace(/\s+/g, ' ').trim() : '';
    var parts = sub ? [].slice.call(sub.querySelectorAll('a')) : [];
    var date = li.dataset.date ? 'Первый визит: ' + li.dataset.date : 'Ещё впереди';
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
    if (parts.length) {
      var ps = document.createElement('small'); ps.className = 'parts';
      ps.appendChild(document.createTextNode('Части: '));
      parts.forEach(function (x, i) {
        if (i) ps.appendChild(document.createTextNode(' · '));
        var pa = document.createElement('a'); pa.href = x.getAttribute('href'); pa.textContent = x.textContent;
        ps.appendChild(pa);
      });
      t.appendChild(ps);
    }
  }
  // Наведение с задержкой: карточка остаётся на последнем регионе, пока мышь идёт к её ссылкам
  // через соседние регионы, и меняется, только если задержаться на другом регионе.
  var hovered = null, hoverTimer = null;
  function hoverTo(code) {
    clearTimeout(hoverTimer);
    if (hovered === null) { hovered = code; show(code); mark(code); return; }
    hoverTimer = setTimeout(function () { hovered = code; show(code); mark(code); }, 250);
  }
  var box = svg.closest('.mapbox') || svg.parentNode;
  box.addEventListener('pointerleave', function (ev) {
    if (ev.pointerType !== 'mouse' || picked) return;
    clearTimeout(hoverTimer); hovered = null; card.innerHTML = hint; mark('');
  });
  function mark(code) {
    paths.forEach(function (p) { p.classList.toggle('on', p.dataset.code === code); });
  }
  function go(code) {
    var href = linkOf(code);
    if (href) location.href = href;
  }

  paths.forEach(function (p) {
    var code = p.dataset.code;
    p.addEventListener('pointerenter', function (ev) { if (ev.pointerType === 'mouse' && !picked) hoverTo(code); });
    p.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse') clearTimeout(hoverTimer); });
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

  // хронология: ползунок по датам первого визита, регионы накопительно, как в атласе
  var dates = [], seen = {};
  items.forEach(function (li) { var d = li.dataset.iso; if (d && !seen[d]) { seen[d] = 1; dates.push(d); } });
  dates.sort();
  var N = dates.length;                     // значение ползунка N = «все даты»
  var track = document.getElementById('track'), tdate = document.getElementById('tdate'), tnote = document.getElementById('tnote');
  var playBtn = document.getElementById('play'), tall = document.getElementById('tall');
  var idx = N, playing = false, timer = null, STEP = 1050;
  var MON = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
  function fmt(iso) { var a = iso.split('-'); return +a[2] + ' ' + MON[a[1] - 1] + ' ' + a[0]; }
  // Шкала по календарю: каждому году равная доля полосы, ползунок считает дни. Шаги ‹ › и воспроизведение
  // по-прежнему идут от поездки к поездке. По числу поездок 2024–2026 сжимались в край под одной подписью.
  function dayNum(iso) { var a = iso.split('-'); return Date.UTC(+a[0], a[1] - 1, +a[2]) / 864e5; }
  var Y0 = +dates[0].slice(0, 4), Y1 = +dates[N - 1].slice(0, 4);
  var D0 = dayNum(Y0 + '-01-01'), DMAX = dayNum(Y1 + '-12-31') - D0;
  var dayOf = dates.map(function (d) { return dayNum(d) - D0; });
  function posOf(i) { return i < N ? dayOf[i] : DMAX; }
  function idxAt(v) {                        // последняя поездка не позже выбранного дня; конец полосы — «все даты»
    if (v >= DMAX) return N;
    var i = 0;
    while (i + 1 < N && dayOf[i + 1] <= v) i++;
    return i;
  }
  track.min = 0; track.max = DMAX; track.step = 1; track.value = DMAX;
  var ruler = document.getElementById('ruler');
  for (var y = Y0; y <= Y1; y++) {
    var s = document.createElement('span'), c = document.createElement('b');
    c.textContent = String(y).slice(0, 2);   // «20» прячется на узком экране: остаётся «’22»
    s.appendChild(c); s.appendChild(document.createTextNode(String(y).slice(2)));
    s.style.left = (dayNum(y + '-01-01') - D0) / DMAX * 100 + '%';
    ruler.appendChild(s);
  }
  function fitRuler() { ruler.classList.toggle('short', ruler.clientWidth / (Y1 - Y0 + 1) < 48); }
  fitRuler();
  window.addEventListener('resize', fitRuler);
  dayOf.forEach(function (d) {               // засечка на каждую дату поездки
    var t = document.createElement('i');
    t.style.left = d / DMAX * 100 + '%';
    ruler.appendChild(t);
  });
  var total = paths.filter(function (p) { return p.dataset.year; }).length;

  function draw() {
    var cur = idx < N ? dates[idx] : null;
    paths.forEach(function (p) {
      var iso = byCode[p.dataset.code] && byCode[p.dataset.code].dataset.iso;
      p.classList.toggle('later', !!(cur && iso && iso > cur));
      p.classList.toggle('arr', !!(cur && iso === cur));
    });
    items.forEach(function (li) { li.hidden = !!(cur && li.dataset.iso && li.dataset.iso > cur) || !okFilter(li); });
    secs.forEach(function (s) { s.hidden = !s.querySelector('li.reg:not([hidden])'); });
    track.value = posOf(idx); tall.hidden = idx >= N; playBtn.classList.toggle('playing', playing); playBtn.setAttribute('aria-label', playing ? 'Пауза' : 'Воспроизвести');
    document.getElementById('tprev').disabled = idx <= 0;
    document.getElementById('tnext').disabled = idx >= N;
    if (!cur) { tdate.textContent = 'Все даты'; tnote.textContent = 'На карте все посещённые регионы.'; if (!picked) card.innerHTML = hint; return; }
    var shown = items.filter(function (li) { return li.dataset.iso && li.dataset.iso <= cur; }).length;
    var arrived = items.filter(function (li) { return li.dataset.iso === cur; });
    tdate.textContent = fmt(cur);
    tnote.textContent = 'Показано ' + shown + ' из ' + total + ' регионов, накопительно.';
    show(arrived[0].dataset.code);
    var extra = arrived.slice(1).map(function (li) { return li.querySelector('.nm, a:not(.code)').textContent; });
    if (extra.length) { var s = card.querySelector('small'); if (s) s.textContent += ' · ещё: ' + extra.join(', '); }
  }
  function okFilter(el) { return (!state.fo || el.dataset.fo === state.fo) && (!state.year || el.dataset.year === state.year); }
  function setIdx(n) { idx = Math.max(0, Math.min(N, n)); draw(); }
  function stopPlay() { playing = false; clearTimeout(timer); }
  function loop() {
    if (!playing) return;
    if (idx >= N) { stopPlay(); draw(); return; }
    timer = setTimeout(function () { idx++; draw(); loop(); }, STEP);
  }
  playBtn.addEventListener('click', function () {
    if (playing) { stopPlay(); draw(); return; }
    if (idx >= N - 1) idx = 0;                    // с конца начинаем заново
    resetFilters(); picked = null; mark('');
    playing = true; draw(); loop();
  });
  track.addEventListener('input', function () { stopPlay(); resetFilters(); picked = null; mark(''); setIdx(idxAt(+track.value)); });
  document.getElementById('tprev').addEventListener('click', function () { stopPlay(); resetFilters(); setIdx(idx - 1); });
  document.getElementById('tnext').addEventListener('click', function () { stopPlay(); resetFilters(); setIdx(idx + 1); });
  tall.addEventListener('click', function () { stopPlay(); setIdx(N); });
  function resetFilters() {
    state.fo = ''; state.year = '';
    [].forEach.call(document.querySelectorAll('.chip'), function (x) { x.setAttribute('aria-pressed', x.dataset.v === '' ? 'true' : 'false'); });
    paths.forEach(function (p) { p.classList.remove('dim'); });
  }
  // выбор фильтра сбрасывает хронологию
  [].forEach.call(document.querySelectorAll('.chip'), function (c) {
    c.addEventListener('click', function () { stopPlay(); idx = N; draw(); apply(); });
  });
  draw();
})();
