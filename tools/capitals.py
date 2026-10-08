#!/usr/bin/env python3
"""Столицы регионов на карте главной -> data/capitals-xy.json (код -> [x, y, название]).

  python tools/capitals.py

Координаты столиц (data/capitals.json: широта, долгота, название) переводятся в ту же систему, что и data/map.json:
проекция Ламберта из tools/favicon.py и линейный перевод в сетку карты. Коэффициенты подбираются по центрам
регионов из data/regions-geo.json: средняя ошибка около 0,4 пикселя на 84 регионах. Регионы, где центр тяжести
сбит (Якутия через линию перемены дат, Чукотка), в подборе не участвуют, но их столицы считаются той же формулой.
Запускать после смены контуров регионов или списка столиц.
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from favicon import lcc                 # та же проекция, что у контуров карты

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

def load(name):
    return json.load(open(os.path.join(DATA, name), encoding='utf-8'))

def main():
    mp = load('map.json')
    geo = load('regions-geo.json')          # код -> кольца [широта, долгота]
    cap = load('capitals.json')             # код -> [широта, долгота, название]
    centre = {r['code']: (r['cx'], r['cy']) for r in mp['regions']}
    X, P = [], []
    for code, rings in geo.items():
        if code not in centre: continue
        pts = np.array([lcc(p[1], p[0]) for r in rings for p in r])
        X.append([pts[:, 0].mean(), pts[:, 1].mean(), 1.0]); P.append(centre[code])
    X, P = np.array(X), np.array(P)
    keep = np.ones(len(X), bool)
    for _ in range(5):                      # отбрасываем выбросы, пока остаются ошибки крупнее 12 пикселей
        A = np.linalg.lstsq(X[keep], P[keep], rcond=None)[0]
        err = np.sqrt(((X @ A - P) ** 2).sum(1))
        keep = err < 12
    print(f'регионов в подборе: {keep.sum()} из {len(X)}, средняя ошибка {err[keep].mean():.2f} px')
    out = {}
    for code, (la, lo, name) in cap.items():
        x, y = lcc(lo, la)
        vx, vy = np.array([x, y, 1.0]) @ A
        out[code] = [round(float(vx), 1), round(float(vy), 1), name]
    with open(os.path.join(DATA, 'capitals-xy.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print(f'столиц: {len(out)} -> data/capitals-xy.json')

if __name__ == '__main__':
    main()
