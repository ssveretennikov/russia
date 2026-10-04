#!/usr/bin/env python3
"""Значок сайта: силуэт России из GeoJSON с границами регионов.

  python tools/favicon.py путь/к/regions.geojson   ->  favicon.png (64x64), apple-touch-icon.png (180x180)

Проекция коническая (Ламберта), как на обычных картах России. Все регионы рисуются одной маской,
поэтому швы между ними пропадают. Нужен только Pillow.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLOR = (184, 117, 18)

def lcc(lon, lat, lon0=100.0, lat0=55.0, p1=52.0, p2=64.0):
    r = math.radians
    if lon < 0: lon += 360.0           # Чукотка за линией перемены дат
    n = math.log(math.cos(r(p1)) / math.cos(r(p2))) / math.log(math.tan(math.pi/4 + r(p2)/2) / math.tan(math.pi/4 + r(p1)/2))
    F = math.cos(r(p1)) * math.tan(math.pi/4 + r(p1)/2) ** n / n
    rho = F / math.tan(math.pi/4 + r(lat)/2) ** n
    rho0 = F / math.tan(math.pi/4 + r(lat0)/2) ** n
    th = n * r(lon - lon0)
    return rho * math.sin(th), -(rho0 - rho * math.cos(th))

def rings(geom):
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        yield poly[0]

def mask(features, side, pad):
    pr = [[lcc(x, y) for x, y in r] for f in features for r in rings(f['geometry'])]
    xs = [x for r in pr for x, _ in r]; ys = [y for r in pr for _, y in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = (side - 2*pad) / max(x1 - x0, y1 - y0)
    ox = (side - (x1 - x0) * k) / 2; oy = (side - (y1 - y0) * k) / 2
    m = Image.new('L', (side, side), 0); d = ImageDraw.Draw(m)
    for r in pr:
        d.polygon([(ox + (x - x0) * k, oy + (y1 - y) * k) for x, y in r], fill=255)
    return m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))   # закрывает щели между регионами

def icon(m, side, background=None):
    a = m.resize((side, side), Image.LANCZOS)
    im = Image.new('RGBA', (side, side), background or (0, 0, 0, 0))
    im.paste(Image.new('RGBA', (side, side), COLOR + (255,)), mask=a)
    return im

def main():
    g = json.load(open(sys.argv[1], encoding='utf-8'))
    m = mask(g['features'], 1024, 40)
    icon(m, 64).save(os.path.join(ROOT, 'favicon.png'), optimize=True)
    big = mask(g['features'], 1024, 190)
    icon(big, 180, (255, 252, 245, 255)).convert('RGB').save(os.path.join(ROOT, 'apple-touch-icon.png'), optimize=True)
    print('готово: favicon.png, apple-touch-icon.png')

if __name__ == '__main__':
    main()
