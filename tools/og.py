#!/usr/bin/env python3
"""Обложки для пересылки ссылок (1200x630): og.jpg для главной и <slug>/og.jpg для региона.

  python tools/og.py            # все
Берёт главный кадр региона (hero из <slug>/media), накладывает код и название.
Шрифт: ищет жирный из списка, иначе берёт встроенный (тогда буквы мельче и проще).
"""
import os, sys, re
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import build as B

FONTS = ['C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf',
         '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
W, H = 1200, 630
OCHRE = (184, 117, 18)

def font(size):
    for f in FONTS:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)

def wrap(draw, text, fnt, width):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if draw.textlength(t, font=fnt) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def badge(draw, x, y, text, size):
    f = font(size); w = int(draw.textlength(text, font=f))
    pad = size // 3; bw, bh = w + pad * 2, int(size * 1.35)
    draw.rounded_rectangle((x, y, x + bw, y + bh), radius=size // 5, fill=OCHRE)
    draw.text((x + pad, y + bh // 2), text, font=f, fill='white', anchor='lm')
    return bw, bh

def cover(photo, code, title, sub, out):
    im = Image.open(photo).convert('RGB')
    sc = W / im.width; im = im.resize((W, round(im.height * sc)), Image.LANCZOS)
    top = max(0, round((im.height - H) * 0.42)); im = im.crop((0, top, W, top + H))
    sh = Image.new('L', (1, H))
    for y in range(H):
        sh.putpixel((0, y), int(200 * max(0, (y - H * 0.35) / (H * 0.65)) ** 1.3))
    im.paste(Image.new('RGB', (W, H), (10, 12, 16)), mask=sh.resize((W, H)))
    d = ImageDraw.Draw(im)
    x, y = 56, H - 56
    ft = font(64); lines = wrap(d, title, ft, W - 112 - 190)
    block = len(lines) * 74
    by = y - block - 36
    if code:
        badge(d, x, by - 120, code, 84)
    for i, ln in enumerate(lines):
        d.text((x, by + i * 74 + 40), ln, font=ft, fill='white', anchor='lm')
    d.text((x, y), sub, font=font(30), fill=(235, 235, 235), anchor='ls')
    im.save(out, 'JPEG', quality=84, optimize=True)
    print('готово:', os.path.relpath(out, ROOT))

def main():
    # python tools/og.py 23-krasnodar 50-moscow-oblast — только эти страницы: у регионов из другой сессии медиа может ещё не быть
    only = set(sys.argv[1:])
    for pg in B.PAGES:
        if only and pg['slug'] not in only: continue
        src = open(os.path.join(ROOT, 'src', pg['slug'] + '.html'), encoding='utf-8').read()
        code = re.search(r'<span class="code"[^>]*>(\d+)</span>', src).group(1)
        name = re.sub(r'<.*?>', '', re.search(r'<h1>(.*?)</h1>', src).group(1))
        places = re.sub(r'<.*?>', '', re.search(r'<div class="reg-places">(.*?)</div>', src).group(1))
        hero = re.search(r'<figure class="hero-ph"[^>]*>.*?<img src="([^"]+)"', src, re.S).group(1)
        cover(os.path.join(ROOT, pg['slug'], hero), code, name, places, os.path.join(ROOT, pg['slug'], 'og.jpg'))
    if only: return
    # главная: кадр последнего готового региона и название серии
    pg = B.PAGES[-1]
    src = open(os.path.join(ROOT, 'src', pg['slug'] + '.html'), encoding='utf-8').read()
    hero = re.search(r'<figure class="hero-ph"[^>]*>.*?<img src="([^"]+)"', src, re.S).group(1)
    cover(os.path.join(ROOT, pg['slug'], hero), None, B.SERIES_TITLE, 'Отчёты о поездках по регионам России', os.path.join(ROOT, 'og.jpg'))

if __name__ == '__main__':
    main()
