#!/usr/bin/env python3
"""Один шаг автора после того, как страницы написаны: экспорт медиа, обложки, сборка, коммит, пуш.

  python tools/publish.py                       # все регионы, где selection.tsv новее media.tsv (или media.tsv нет)
  python tools/publish.py 02-bashkortostan 03-buryatia   # только эти
  python tools/publish.py --no-push             # всё то же, но без git

Делает по каждому региону: tools/media.py export <slug>; затем tools/og.py, build.py;
затем git add <slug>/ regions/<slug>/media.tsv, коммит «Медиа: …» и push в текущую ветку.
"""
import os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(*cmd, check=True):
    print('>', ' '.join(map(str, cmd))); sys.stdout.flush()
    r = subprocess.run(list(map(str, cmd)), cwd=ROOT)
    if check and r.returncode: sys.exit(f'ошибка: {" ".join(map(str, cmd))}')
    return r.returncode


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; push = '--no-push' not in sys.argv
    slugs = args or sorted(d.name for d in (ROOT / 'regions').iterdir() if (d / 'selection.tsv').exists()
                           and (not (d / 'media.tsv').exists() or (d / 'selection.tsv').stat().st_mtime > (d / 'media.tsv').stat().st_mtime))
    if not slugs: sys.exit('нечего экспортировать: нет регионов с новым selection.tsv')
    print('регионы:', ', '.join(slugs))
    done = []
    for s in slugs:
        if run(PY, ROOT / 'tools' / 'media.py', 'export', s, check=False) == 0: done.append(s)
        else: print(f'!! экспорт {s} не удался, регион пропущен')
    if not done: sys.exit('ни один экспорт не прошёл')
    run(PY, ROOT / 'tools' / 'og.py'); run(PY, ROOT / 'build.py')
    for s in done:
        empty = [f for f in (ROOT / s / 'media').iterdir() if f.stat().st_size == 0]
        if empty: print(f'!! {s}: пустые файлы: {", ".join(f.name for f in empty)}')
    if not push: return
    paths = [p for s in done for p in (s, f'regions/{s}/media.tsv')] + ['index.html', 'sitemap.xml', '404.html']
    paths += [str(p.relative_to(ROOT)) for p in ROOT.glob('*/index.html') if (ROOT / 'src' / (p.parent.name + '.html')).exists()]
    run('git', 'add', *paths)
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0: print('нечего коммитить'); return
    run('git', 'commit', '-q', '-m', 'Медиа и сборка: ' + ', '.join(done))
    branch = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    run('git', 'push', 'origin', branch)
    print('готово:', ', '.join(done))


if __name__ == '__main__': main()
