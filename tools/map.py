#!/usr/bin/env python3
"""Карта для главной: контуры регионов из GeoJSON атласа -> data/map.json.

  python tools/map.py путь/к/regions_with_dates_updated.geojson

Проекция коническая (Ламберта), как в tools/favicon.py. Контуры упрощаются (Дуглас — Пекер),
координаты округляются до десятых долей пикселя в сетке 1000 по ширине. Нужен numpy.
В JSON: viewBox карты и по каждому региону код, путь (d), дата первого визита, центр.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from favicon import lcc, rings          # та же проекция

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = 1000.0          # ширина карты в пикселях сетки
TOL = 0.6           # допуск упрощения, px
MIN_AREA = 0.5      # мелкие острова (px^2) отбрасываем, кроме единственного контура региона

def dp(pts, tol):
    """Дуглас — Пекер без рекурсии; pts — массив (n, 2)."""
    n = len(pts)
    if n < 3: return pts
    keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1: continue
        p, q = pts[a], pts[b]
        seg = pts[a + 1:b]
        d = q - p; L = np.hypot(*d)
        dist = np.hypot(*(seg - p).T) if L == 0 else np.abs(d[0] * (seg[:, 1] - p[1]) - d[1] * (seg[:, 0] - p[0])) / L
        i = int(np.argmax(dist))
        if dist[i] > tol:
            k = a + 1 + i; keep[k] = True
            stack += [(a, k), (k, b)]
    return pts[keep]

def area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def path(rs):
    out = []
    for r in rs:
        r = np.round(r, 1)
        s = f'M{r[0][0]:g} {r[0][1]:g}'
        prev = r[0]
        for p in r[1:]:
            dx, dy = round(p[0] - prev[0], 1), round(p[1] - prev[1], 1)
            if dx or dy: s += f'l{dx:g} {dy:g}'
            prev = p
        out.append(s + 'z')
    return ''.join(out)

def main():
    g = json.load(open(sys.argv[1], encoding='utf-8'))
    raw = []
    for f in g['features']:
        rs = [np.array([lcc(x, y) for x, y in r]) for r in rings(f['geometry'])]
        raw.append((f['properties'], rs))
    allp = np.vstack([r for _, rs in raw for r in rs])
    x0, y0 = allp.min(0); x1, y1 = allp.max(0)
    k = W / (x1 - x0); H = (y1 - y0) * k
    items = []
    for p, rs in raw:
        rs = [np.column_stack(((r[:, 0] - x0) * k, (r[:, 1] - y0) * k)) for r in rs]
        areas = [area(r) for r in rs]
        big = max(areas)
        rs = [dp(r, TOL) for r, a in zip(rs, areas) if a >= MIN_AREA or a == big]
        rs = [r for r in rs if len(r) >= 3]
        main = max(rs, key=area)
        items.append(dict(code=str(p['vehicle_region_code']), name=p['subject_name_ru'],
                          date=p['start_date'], area=float(sum(area(r) for r in rs)),
                          cx=round(float(main[:, 0].mean()), 1), cy=round(float(main[:, 1].mean()), 1),
                          d=path(rs)))
    items.sort(key=lambda i: -i['area'])             # крупные снизу, мелкие (города) сверху
    for i in items:
        i['tiny'] = int(i['area'] < 250)               # города и малые республики: рисуем с обводкой, чтобы в них можно было попасть
        del i['area']
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    out = os.path.join(ROOT, 'data', 'map.json')
    json.dump(dict(w=int(W), h=round(H), regions=items), open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('готово: data/map.json', os.path.getsize(out) // 1024, 'КБ,', len(items), 'регионов, карта', int(W), 'x', round(H))

if __name__ == '__main__':
    main()
