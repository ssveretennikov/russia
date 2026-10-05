#!/usr/bin/env python3
"""Миниатюры для главной (360x270, WebP): <slug>/thumb.webp.

  python tools/thumbs.py            # недостающие и устаревшие
  python tools/thumbs.py --force    # все заново
Главный кадр весит 64–709 КБ — на главную с её девятью десятками регионов он не годится.
Кадр тот же, что у обложки (tools/og.py): заданный в PAGES как og, иначе главный; кадрирование то же.
"""
import os, sys, re
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build as B

W, H = 360, 270          # вдвое больше места на экране: на телефонах с плотным экраном не мылится
QUALITY = 72

def hero_of(pg):
    src = open(os.path.join(ROOT, 'src', pg['slug'] + '.html'), encoding='utf-8').read()
    return pg.get('og') or re.search(r'<figure class="hero-ph"[^>]*>.*?<img src="([^"]+)"', src, re.S).group(1)

def thumb(photo, out):
    im = Image.open(photo).convert('RGB')
    sc = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    left = (im.width - W) // 2
    top = max(0, round((im.height - H) * 0.42))     # как у обложки: чуть выше середины, где обычно главное
    im.crop((left, top, left + W, top + H)).save(out, 'WEBP', quality=QUALITY, method=6)

def main():
    force = '--force' in sys.argv
    made = 0
    for pg in B.PAGES:
        photo = os.path.join(ROOT, pg['slug'], hero_of(pg))
        out = os.path.join(ROOT, pg['slug'], 'thumb.webp')
        if not force and os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(photo):
            continue
        thumb(photo, out); made += 1
    sizes = [os.path.getsize(os.path.join(ROOT, pg['slug'], 'thumb.webp')) for pg in B.PAGES]
    print(f'сделано: {made}, всего: {len(sizes)}, вес: {sum(sizes) // 1024} КБ, самая тяжёлая: {max(sizes) // 1024} КБ')

if __name__ == '__main__':
    main()
