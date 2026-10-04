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
})();
