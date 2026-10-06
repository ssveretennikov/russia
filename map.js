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
  var state = { fo: '', year: '', q: '' };
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
    var cap = li.dataset.cap || '';
    var parts = sub ? [].slice.call(sub.querySelectorAll('a')) : [];
    var date = li.dataset.home ? 'Дом — отсюда начинаются поездки'
      : li.dataset.date ? 'В отчёте: ' + li.dataset.date : 'Ещё впереди';
    var tr = TR[li.dataset.tr];
    if (tr) date += ' · ' + tr.icon + ' ' + tr.text;
    card.innerHTML = '';
    var th = li.querySelector('img.th');
    if (th) {
      var im = document.createElement('img'); im.className = 'mth'; im.alt = ''; im.src = th.getAttribute('src');
      card.appendChild(im);
    }
    var t = document.createElement('div'); t.className = 'mt';
    var h = document.createElement('div'); h.className = 'mh';     // номер рядом с названием: на телефоне рядом с фото отдельной колонке нет места
    var b = document.createElement('span'); b.className = 'code'; b.textContent = code;
    var n = document.createElement('strong'); n.textContent = name ? name.textContent : code;
    var s = document.createElement('small'); s.textContent = [cap, date].filter(Boolean).join(' · ');
    h.appendChild(b); h.appendChild(n);
    t.appendChild(h); t.appendChild(s);
    card.appendChild(t);
    if (href) {
      var a = document.createElement('a'); a.className = 'go'; a.href = href;
      a.textContent = 'Открыть отчёт →';
      card.appendChild(a);
    }
    if (parts.length) {
      var ps = document.createElement('small'); ps.className = 'parts';
      ps.appendChild(document.createTextNode('Ещё: '));
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

  // Увеличение. На телефоне регионы центра и Кавказа мельче пальца, поэтому выбор округа
  // приближает карту к нему, а кнопка — к европейской части. Пропорции окна не меняются: страница не прыгает.
  var vb0 = svg.viewBox.baseVal, W = vb0.width, H = vb0.height, FULL = [0, 0, W, H];
  var EUROPE = [0, 100, 340, 330];             // x, y, ширина, высота; арктические острова Архангельской области не в счёт
  var zoomBtn = document.getElementById('zoom'), view = FULL.slice(), zoomed = false, anim = 0;
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function fit(b) {
    var pad = Math.max(b[2], b[3]) * 0.06, x = b[0] - pad, y = b[1] - pad, w = b[2] + 2 * pad, h = b[3] + 2 * pad;
    if (w / h < W / H) { x -= (h * W / H - w) / 2; w = h * W / H; } else { y -= (w * H / W - h) / 2; h = w * H / W; }
    return w >= W ? FULL : [x, y, w, h];
  }
  function foBox(fo) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    paths.forEach(function (p) {
      if (p.dataset.fo !== fo) return;
      var b = p.getBBox();
      x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y); x1 = Math.max(x1, b.x + b.width); y1 = Math.max(y1, b.y + b.height);
    });
    return [x0, y0, x1 - x0, y1 - y0];
  }
  function setView(v) { view = v; svg.setAttribute('viewBox', v.join(' ')); }
  function zoomTo(target) {
    cancelAnimationFrame(anim);
    zoomed = target !== FULL;
    zoomBtn.textContent = zoomed ? 'Вся страна' : 'Европейская часть';
    if (still) { setView(target); return; }
    var from = view.slice(), t0 = null;
    anim = requestAnimationFrame(function step(ts) {
      if (t0 === null) t0 = ts;
      var k = Math.min(1, (ts - t0) / 350), e = 1 - Math.pow(1 - k, 3);
      setView(from.map(function (a, i) { return a + (target[i] - a) * e; }));
      if (k < 1) anim = requestAnimationFrame(step);
    });
  }
  zoomBtn.addEventListener('click', function () { zoomTo(zoomed ? FULL : fit(EUROPE)); });

  // «К карте»: список длинный, на телефоне — несколько тысяч точек; кнопка видна, когда карта ушла за верх экрана
  var totop = document.getElementById('totop');
  function onScroll() { totop.hidden = box.getBoundingClientRect().bottom > 0; }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  paths.forEach(function (p) {
    var code = p.dataset.code;
    p.addEventListener('pointerenter', function (ev) { if (ev.pointerType === 'mouse' && !picked) hoverTo(code); });
    p.addEventListener('pointerleave', function (ev) { if (ev.pointerType === 'mouse') clearTimeout(hoverTimer); });
    p.addEventListener('focus', function () { show(code); mark(code); });
    p.addEventListener('click', function (ev) {
      if (ev.pointerType === 'touch' || ev.pointerType === 'pen') { picked = code; show(code); mark(code); card.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); return; }
      go(code);
    });
    p.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); go(code); } });
  });
  document.addEventListener('click', function (ev) {
    if (picked && !ev.target.closest('.rumap, .mcard')) { picked = null; card.innerHTML = hint; mark(''); }
  });

  // фильтры
  function apply() {
    paths.forEach(function (p) { p.classList.toggle('dim', !okFilter(p)); });
    items.forEach(function (li) { li.hidden = !okFilter(li); });
    secs.forEach(function (s) { s.hidden = !s.querySelector('li.reg:not([hidden])'); });
    none.hidden = items.some(function (li) { return !li.hidden; });
    syncFav();
  }

  // Лента «Любимые» — для первого взгляда на всю страну. Когда читатель что-то ищет, выбрал округ или год
  // или смотрит «Путь по годам», лента убирается, чтобы найденное стояло сразу под поиском.
  var fav = document.getElementById('fav'), favRow = document.getElementById('favRow');
  var favNav = document.getElementById('favNav'), favPrev = document.getElementById('favPrev'), favNext = document.getElementById('favNext');
  function favStep() {
    // листаем на столько карточек, сколько целиком помещается в ленте: на компьютере — по три
    var cards = favRow.querySelectorAll('.fc');
    if (cards.length < 2) return favRow.clientWidth;
    var pitch = cards[1].offsetLeft - cards[0].offsetLeft, gap = pitch - cards[0].offsetWidth;
    return Math.max(1, Math.floor((favRow.clientWidth + gap + 1) / pitch)) * pitch;
  }
  function favSyncNav() {
    if (!fav) return;
    var max = favRow.scrollWidth - favRow.clientWidth;
    favPrev.disabled = favRow.scrollLeft <= 2;
    favNext.disabled = favRow.scrollLeft >= max - 2;
    favNav.hidden = max <= 2;
  }
  function syncFav() {
    if (!fav) return;
    var busy = !!(state.fo || state.year || state.q) || idx < N;
    if (fav.hidden !== busy) fav.hidden = busy;
    if (!busy) favSyncNav();
  }
  if (fav) {
    favPrev.addEventListener('click', function () { favRow.scrollBy({ left: -favStep(), behavior: 'smooth' }); });
    favNext.addEventListener('click', function () { favRow.scrollBy({ left: favStep(), behavior: 'smooth' }); });
    favRow.addEventListener('scroll', favSyncNav, { passive: true });
    window.addEventListener('resize', favSyncNav);
  }
  // поиск по названию и столице; строка поиска в атрибуте data-q уже строчная и с «е» вместо «ё»
  var find = document.getElementById('find'), none = document.getElementById('none');
  find.addEventListener('input', function () {
    state.q = find.value.trim().toLowerCase().replace(/ё/g, 'е');
    stopPlay(); idx = N; draw(); apply();
  });
  [].forEach.call(document.querySelectorAll('.chip'), function (c) {
    c.addEventListener('click', function () {
      state[c.dataset.k] = c.dataset.v;
      [].forEach.call(document.querySelectorAll('.chip[data-k="' + c.dataset.k + '"]'), function (x) {
        x.setAttribute('aria-pressed', x === c ? 'true' : 'false');
      });
      apply();
      if (c.dataset.k === 'fo') zoomTo(c.dataset.v ? fit(foBox(c.dataset.v)) : FULL);
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
  var MON1 = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
  // «Путь по годам» под картой — та же кнопка воспроизведения, что в хронологии: та под карточкой, её не замечали
  var story = document.getElementById('story'), mapdate = document.getElementById('mapdate');
  story.addEventListener('click', function () { playBtn.click(); });
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
  var total = items.filter(function (li) { return li.dataset.iso; }).length;   // по списку: у дома (Москвы) нет года, но он посещён

  function draw() {
    var cur = idx < N ? dates[idx] : null;
    paths.forEach(function (p) {
      var iso = byCode[p.dataset.code] && byCode[p.dataset.code].dataset.iso;
      p.classList.toggle('later', !!(cur && iso && iso > cur));
      p.classList.toggle('arr', !!(cur && iso === cur && !byCode[p.dataset.code].dataset.home));
    });
    items.forEach(function (li) { li.hidden = !!(cur && li.dataset.iso && li.dataset.iso > cur) || !okFilter(li); });
    secs.forEach(function (s) { s.hidden = !s.querySelector('li.reg:not([hidden])'); });
    syncFav();
    track.value = posOf(idx); tall.hidden = idx >= N; playBtn.classList.toggle('playing', playing); playBtn.setAttribute('aria-label', playing ? 'Пауза' : 'Воспроизвести');
    story.classList.toggle('playing', playing);
    mapdate.hidden = !cur;
    if (cur) {
      var a = cur.split('-');
      mapdate.textContent = MON1[a[1] - 1] + ' ' + a[0];
      var sm = document.createElement('small');
      sm.textContent = items.filter(function (li) { return li.dataset.iso && li.dataset.iso <= cur; }).length + ' из ' + total + ' регионов';
      mapdate.appendChild(sm);
    }
    document.getElementById('tprev').disabled = idx <= 0;
    document.getElementById('tnext').disabled = idx >= N;
    if (!cur) { tdate.textContent = 'Все даты'; tnote.textContent = 'На карте все посещённые регионы.'; if (!picked) card.innerHTML = hint; return; }
    var shown = items.filter(function (li) { return li.dataset.iso && li.dataset.iso <= cur; }).length;
    var arrived = items.filter(function (li) { return li.dataset.iso === cur && !li.dataset.home; });
    tdate.textContent = fmt(cur);
    tnote.textContent = 'Показано ' + shown + ' из ' + total + ' регионов, накопительно.';
    show(arrived[0].dataset.code);
    var extra = arrived.slice(1).map(function (li) { return li.querySelector('.nm, a:not(.code)').textContent; });
    if (extra.length) { var s = card.querySelector('small'); if (s) s.textContent += ' · ещё: ' + extra.join(', '); }
  }
  function okFilter(el) {
    var li = byCode[el.dataset.code];          // у контура на карте строки поиска нет — берётся из строки списка
    return (!state.fo || el.dataset.fo === state.fo) && (!state.year || el.dataset.year === state.year)
      && (!state.q || (li && li.dataset.q.indexOf(state.q) >= 0));
  }
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
    var hadFo = state.fo;
    state.fo = ''; state.year = '';
    [].forEach.call(document.querySelectorAll('.chip'), function (x) { x.setAttribute('aria-pressed', x.dataset.v === '' ? 'true' : 'false'); });
    paths.forEach(function (p) { p.classList.remove('dim'); });
    if (hadFo) zoomTo(FULL);   // округ снят — снимается и его увеличение; «Европейскую часть» хронология не трогает
  }
  // выбор фильтра сбрасывает хронологию
  [].forEach.call(document.querySelectorAll('.chip'), function (c) {
    c.addEventListener('click', function () { stopPlay(); idx = N; draw(); apply(); });
  });
  draw();
})();
