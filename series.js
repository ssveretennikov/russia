/* Серия отчётов по регионам. Единственная функция: показать или скрыть пометки для автора. */
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
