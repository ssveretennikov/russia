#!/usr/bin/env python3
"""Работа с фото- и видеоархивом региона. Модель не тратит токены на то, что умеет скрипт.

  python tools/media.py check
  python tools/media.py inventory 49-magadan            # миниатюры, контактные листы, timeline.md
  python tools/media.py detail 49-magadan P159 P731 --size 1700
  python tools/media.py detail 49-magadan P622 P623 P002 --sheet cand1   # лист кандидатов 4 в ряд
  python tools/media.py vstrip 49-magadan V46 --n 10    # раскадровка видео, чтобы выбрать фрагмент
  python tools/media.py export 49-magadan               # по selection.tsv -> <регион>/media/

Источник архива: regions/<регион>/source.txt, по одному пути к папке в строке.
Нужны: Python 3.10+, Pillow (pip install pillow pillow-heif), ffmpeg и ffprobe в PATH.
"""
import argparse, json, os, re, shutil, subprocess, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC = True
except Exception:
    HEIC = False

ROOT = Path(__file__).resolve().parent.parent
PHOTO_EXT = {'.jpg', '.jpeg', '.png'} | ({'.heic'} if HEIC else set())
VIDEO_EXT = {'.mp4', '.mov', '.m4v'}
TONEMAP = ('zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,'
           'zscale=t=bt709:m=bt709:r=tv,format=yuv420p')
FALLBACK = 'format=yuv420p,eq=contrast=1.5:saturation=1.4:brightness=-0.05'


def rdir(region): return ROOT / 'regions' / region
def wdir(region, *sub):
    p = rdir(region) / 'work' / Path(*sub); p.mkdir(parents=True, exist_ok=True); return p


def sources(region):
    f = rdir(region) / 'source.txt'
    if not f.exists(): sys.exit(f'Нет файла {f}: впишите в него путь к папке с архивом.')
    out = [Path(l.strip()) for l in f.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]
    for p in out:
        if not p.is_dir(): sys.exit(f'Папка не найдена: {p}')
    return out


def font(size):
    for name in ('DejaVuSans-Bold.ttf', 'arialbd.ttf', 'Arial Bold.ttf', 'arial.ttf'):
        try: return ImageFont.truetype(name, size)
        except Exception: pass
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'C:/Windows/Fonts/arialbd.ttf'):
        if os.path.exists(p): return ImageFont.truetype(p, size)
    try: return ImageFont.load_default(size)
    except TypeError: return ImageFont.load_default()


def scan(region):
    """Все файлы архива в стабильном порядке: сначала корень, потом подпапки, внутри по имени."""
    photos, videos = [], []
    for si, src in enumerate(sources(region)):
        files = sorted((p for p in src.rglob('*') if p.is_file()),
                       key=lambda p: (len(p.relative_to(src).parts), str(p.relative_to(src)).lower()))
        for p in files:
            rel = str(p.relative_to(src)).replace('\\', '/')
            if any(part.startswith(('_', '.')) for part in p.relative_to(src).parts[:-1]): continue
            ext = p.suffix.lower()
            if ext in PHOTO_EXT: photos.append((si, rel, str(p)))
            elif ext in VIDEO_EXT: videos.append((si, rel, str(p)))
    return photos, videos


def name_time(name):
    m = re.search(r'(20\d\d)[-_]?(\d\d)[-_]?(\d\d)[ _-]+(\d\d)[-_:]?(\d\d)[-_:]?(\d\d)', name)
    return f'{m[1]}-{m[2]}-{m[3]} {m[4]}:{m[5]}:{m[6]}' if m else ''


def _gps(ex):
    try:
        g = ex.get_ifd(0x8825)
        def c(v, r):
            d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
            return -d if r in ('S', 'W') else d
        return round(c(g[2], g[1]), 5), round(c(g[4], g[3]), 5), round(float(g.get(6, 0)))
    except Exception:
        return '', '', ''


def _thumb(job):
    pid, path, dst = job
    try:
        im = Image.open(path); ex = im.getexif()
        dt = str(ex.get_ifd(0x8769).get(0x9003) or '')
        dt = (dt[:10].replace(':', '-') + dt[10:]) if dt else name_time(os.path.basename(path))
        lat, lon, alt = _gps(ex); w, h = im.size; model = str(ex.get(0x110) or '')
        if not os.path.exists(dst):
            im.draft('RGB', (640, 640)); im = ImageOps.exif_transpose(im); im.thumbnail((360, 360))
            im.convert('RGB').save(dst, quality=80)
        return pid, dt, lat, lon, alt, w, h, model, ''
    except Exception as e:
        return pid, name_time(os.path.basename(path)), '', '', '', '', '', '', str(e)[:80]


def sheet(items, dst, cols, cell, label_h=26, fsize=19):
    """items: [(подпись, путь к картинке)]"""
    rows = (len(items) + cols - 1) // cols
    sh = Image.new('RGB', (cols * cell, rows * (cell + label_h)), (20, 20, 20)); d = ImageDraw.Draw(sh); f = font(fsize)
    for k, (lab, path) in enumerate(items):
        x, y = (k % cols) * cell, (k // cols) * (cell + label_h)
        try:
            im = Image.open(path).convert('RGB'); im.thumbnail((cell, cell))
            sh.paste(im, (x + (cell - im.width) // 2, y + label_h + (cell - im.height) // 2))
        except Exception: pass
        d.text((x + 4, y + 2), lab, fill=(255, 230, 80), font=f)
    sh.save(dst, quality=82)


def probe(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                        'format=duration,size:stream=width,height,codec_name,r_frame_rate,color_transfer',
                        '-of', 'json', path], capture_output=True, text=True)
    j = json.loads(r.stdout or '{}'); v = next((s for s in j.get('streams', []) if s.get('width')), {})
    return dict(dur=float(j.get('format', {}).get('duration', 0) or 0), size=int(j.get('format', {}).get('size', 0) or 0),
                w=v.get('width', 0), h=v.get('height', 0), hdr=v.get('color_transfer') in ('smpte2084', 'arib-std-b67'))


def ff(args):
    return subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, capture_output=True, text=True)


def frame(path, t, dst, width, hdr):
    """Один кадр; для HDR пробует тонмаппинг, при неудаче — простую коррекцию."""
    base = ['-ss', f'{t:.2f}', '-i', path, '-frames:v', '1', '-q:v', '4']
    sc = f"scale='if(gt(iw,ih),{width},-2)':'if(gt(iw,ih),-2,{width})'"
    for vf in ([f'{sc},{TONEMAP}', f'{sc},{FALLBACK}'] if hdr else [sc]):
        ff(base + ['-vf', vf, dst])
        if os.path.exists(dst) and os.path.getsize(dst) > 0: return True
    return False


def _vframes(job):
    vid, path, out = job
    info = probe(path)
    for i, fr in enumerate((0.15, 0.5, 0.85)):
        dst = os.path.join(out, f'{vid}_{i}.jpg')
        if not os.path.exists(dst):
            ff(['-noaccurate_seek', '-ss', f'{info["dur"] * fr:.2f}', '-skip_frame', 'nokey', '-i', path, '-frames:v', '1',
                '-vf', 'scale=360:360:force_original_aspect_ratio=decrease', '-q:v', '4', dst])
    return vid, info


def cmd_check(a):
    ok = True
    for tool in ('ffmpeg', 'ffprobe'):
        found = shutil.which(tool); ok &= bool(found); print(f'{tool}: {found or "НЕ НАЙДЕН — установите и добавьте в PATH"}')
    import PIL; print('Pillow:', PIL.__version__, '| HEIC:', 'да' if HEIC else 'нет (pip install pillow-heif)')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True).stdout if shutil.which('ffmpeg') else ''
    print('тонмаппинг HDR-видео (zscale):', 'да' if ' zscale ' in r else 'нет — будет простая коррекция цвета')
    sys.exit(0 if ok else 1)


def cmd_inventory(a):
    photos, videos = scan(a.region); th = wdir(a.region, 'thumbs'); sh = wdir(a.region, 'sheets'); vf = wdir(a.region, 'vframes')
    jobs = [(f'P{i + 1:03d}', path, str(th / f'P{i + 1:03d}.jpg')) for i, (_, rel, path) in enumerate(photos)]
    with ProcessPoolExecutor(a.jobs) as ex: meta = list(ex.map(_thumb, jobs, chunksize=4))
    rows = []
    for (si, rel, path), m in zip(photos, meta):
        rows.append([m[0], rel, m[1], *map(str, m[2:9])])
    (rdir(a.region) / 'index.tsv').write_text('id\tfile\ttaken\tlat\tlon\talt\tw\th\tcamera\terror\n' +
                                               '\n'.join('\t'.join(r) for r in rows), encoding='utf-8')
    for p in range(0, len(rows), 30):
        items = []
        for r in rows[p:p + 30]:
            sub = r[1].rsplit('/', 1)[0][:10] + ' ' if '/' in r[1] else ''
            items.append((f'{r[0]} {sub}{r[2][8:10]}.{r[2][5:7]} {r[2][11:16]}' if r[2] else f'{r[0]} {sub}', str(th / f'{r[0]}.jpg')))
        sheet(items, sh / f'p{p // 30 + 1:02d}.jpg', 6, 360)
    vjobs = [(f'V{i + 1:02d}', path, str(vf)) for i, (_, rel, path) in enumerate(videos)]
    with ProcessPoolExecutor(max(1, a.jobs - 1)) as ex: vmeta = dict(ex.map(_vframes, vjobs))
    vrows = []
    for i, (si, rel, path) in enumerate(videos):
        vid = f'V{i + 1:02d}'; m = vmeta[vid]
        vrows.append([vid, rel, name_time(os.path.basename(rel)), f'{m["dur"]:.1f}', f'{m["w"]}x{m["h"]}', 'hdr' if m['hdr'] else '', str(m['size'] // 2 ** 20)])
    (rdir(a.region) / 'vindex.tsv').write_text('id\tfile\ttaken\tseconds\tsize\thdr\tmb\n' + '\n'.join('\t'.join(r) for r in vrows), encoding='utf-8')
    for old in sh.glob('v*.jpg'): old.unlink()
    f = font(18)
    for p in range(0, len(vrows), 12):
        chunk = vrows[p:p + 12]; W = 360; L = 26
        im = Image.new('RGB', (6 * W, ((len(chunk) + 1) // 2) * (W + L)), (20, 20, 20)); d = ImageDraw.Draw(im)
        for k, r in enumerate(chunk):
            col, row = (k % 2) * 3, k // 2
            d.text((col * W + 4, row * (W + L) + 3), f'{r[0]} {r[2][8:10]}.{r[2][5:7]} {r[2][11:16]} {float(r[3]):.0f}s {r[4]}', fill=(255, 230, 80), font=f)
            for i in range(3):
                fp = vf / f'{r[0]}_{i}.jpg'
                if fp.exists():
                    t = Image.open(fp); im.paste(t, ((col + i) * W + (W - t.width) // 2, row * (W + L) + L + (W - t.height) // 2))
        im.save(sh / f'v{p // 12 + 1:02d}.jpg', quality=82)
    # timeline.md: по дням, с точками, где менялось место
    days = {}
    for r in rows:
        if r[2]: days.setdefault(r[2][:10], []).append(r)
    tl = [f'# Хронология архива: {a.region}', '', f'Фото: {len(rows)}, видео: {len(vrows)}. Листы: work/sheets/ (p01… фото, v01… видео).', '']
    subs = sorted({r[1].rsplit('/', 1)[0] for r in rows + vrows if '/' in r[1]})
    if subs: tl += ['Подпапки (часто чужие кадры — проверить авторство): ' + '; '.join(subs), '']
    for day in sorted(days):
        rs = sorted(days[day], key=lambda r: r[2]); tl.append(f'## {day} — {len(rs)} фото, {rs[0][2][11:16]}–{rs[-1][2][11:16]} ({rs[0][0]}…{rs[-1][0]})')
        last = None
        for r in rs:
            if not r[3]: continue
            key = (round(float(r[3]), 2), round(float(r[4]), 2))
            if key != last: tl.append(f'- {r[2][11:16]} {r[0]} — {r[3]}, {r[4]}, высота {r[5]} м'); last = key
        vs = [v for v in vrows if v[2][:10] == day]
        if vs: tl.append('- видео: ' + ', '.join(f'{v[0]} {v[2][11:16]} {float(v[3]):.0f}с' for v in vs))
        tl.append('')
    nodate = [r[0] for r in rows if not r[2]]
    if nodate: tl.append(f'Без даты: {nodate[0]}…{nodate[-1]} ({len(nodate)} шт.)')
    (rdir(a.region) / 'timeline.md').write_text('\n'.join(tl), encoding='utf-8')
    print(f'фото {len(rows)}, видео {len(vrows)}; листов {len(list(sh.glob("*.jpg")))}; ошибок чтения {sum(1 for r in rows if r[9])}')


def load_index(region, name='index.tsv'):
    lines = (rdir(region) / name).read_text(encoding='utf-8').splitlines()[1:]
    srcs = sources(region); out = {}
    for l in lines:
        c = l.split('\t')
        path = next((s / c[1] for s in srcs if (s / c[1]).exists()), srcs[0] / c[1])
        out[c[0]] = (str(path), c)
    return out


def cmd_detail(a):
    idx = load_index(a.region); out = wdir(a.region, 'detail'); items = []
    for pid in a.ids:
        path = idx[pid][0]
        im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
        if a.sheet:
            im.thumbnail((540, 540)); tmp = out / f'_{pid}.jpg'; im.save(tmp, quality=84); items.append((pid, str(tmp)))
        else:
            im.thumbnail((a.size, a.size)); dst = out / f'{pid}_{a.size}.jpg'; im.save(dst, quality=82); print(dst)
    if a.sheet:
        dst = out / f'{a.sheet}.jpg'; sheet(items, dst, 4, 540, 30, 22); print(dst)
        for _, t in items: os.remove(t)


def cmd_vstrip(a):
    idx = load_index(a.region, 'vindex.tsv'); out = wdir(a.region, 'detail'); path = idx[a.vid][0]; info = probe(path); items = []
    for i in range(a.n):
        t = info['dur'] * (i + 0.5) / a.n; tmp = out / f'_{a.vid}_{i}.jpg'
        if frame(path, t, str(tmp), 480, info['hdr']): items.append((f'{t:.1f}s', str(tmp)))
    dst = out / f'{a.vid}_strip.jpg'; sheet(items, dst, 5, 480, 26, 20); print(dst, f'длина {info["dur"]:.1f} c')
    for _, t in items: os.remove(t)


def cmd_export(a):
    """selection.tsv: имя<TAB>ID<TAB>размер[<TAB>отрезки видео «3-11,24-32» в секундах]"""
    pidx = load_index(a.region); vidx = load_index(a.region, 'vindex.tsv') if (rdir(a.region) / 'vindex.tsv').exists() else {}
    out = ROOT / a.region / 'media'; out.mkdir(parents=True, exist_ok=True); rows = []
    for line in (rdir(a.region) / 'selection.tsv').read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'): continue
        c = line.split('\t'); name, mid, size = c[0], c[1], int(c[2])
        if mid.startswith('P'):
            path, meta = pidx[mid]; im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
            im.thumbnail((size, size), Image.LANCZOS); im.save(out / f'{name}.jpg', quality=80, optimize=True, progressive=True)
            rows.append([name, mid, str(im.width), str(im.height), meta[2]])
        else:
            path, meta = vidx[mid]; info = probe(path)
            segs = [tuple(map(float, s.split('-'))) for s in c[3].split(',')] if len(c) > 3 and c[3] else [(0, min(info['dur'], 15))]
            t0, t1 = segs[0][0], segs[-1][1]
            sc = f"scale='if(gt(iw,ih),{size},-2)':'if(gt(iw,ih),-2,{size})',fps=30"
            dst = out / f'{name}.mp4'
            for tone in ([TONEMAP, FALLBACK] if info['hdr'] else ['format=yuv420p']):
                fc = f'[0:v]{sc},{tone},split={len(segs)}' + ''.join(f'[v{i}]' for i in range(len(segs))) + ';'
                fc += f'[0:a]asplit={len(segs)}' + ''.join(f'[a{i}]' for i in range(len(segs))) + ';'
                for i, (s, e) in enumerate(segs):
                    fc += f'[v{i}]trim={s - t0}:{e - t0},setpts=PTS-STARTPTS[x{i}];[a{i}]atrim={s - t0}:{e - t0},asetpts=PTS-STARTPTS[y{i}];'
                fc += ''.join(f'[x{i}][y{i}]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=1[v][a]'
                r = ff(['-ss', str(t0), '-t', str(t1 - t0), '-i', path, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '26', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', str(dst)])
                if r.returncode == 0 and dst.exists(): break
            else:
                print('НЕ УДАЛОСЬ:', name, r.stderr[-300:]); continue
            ff(['-ss', '2', '-i', str(dst), '-frames:v', '1', '-q:v', '3', str(out / f'{name}.jpg')])
            p = probe(str(dst)); rows.append([name, mid, str(p['w']), str(p['h']), meta[2]])
        print(*rows[-1])
    (rdir(a.region) / 'media.tsv').write_text('name\tid\tw\th\ttaken\n' + '\n'.join('\t'.join(r) for r in rows), encoding='utf-8')
    total = sum(f.stat().st_size for f in out.iterdir()) / 2 ** 20
    print(f'готово: {len(rows)} файлов, {total:.0f} МБ в {out}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('check').set_defaults(fn=cmd_check)
    p = sp.add_parser('inventory'); p.add_argument('region'); p.add_argument('--jobs', type=int, default=3); p.set_defaults(fn=cmd_inventory)
    p = sp.add_parser('detail'); p.add_argument('region'); p.add_argument('ids', nargs='+'); p.add_argument('--size', type=int, default=1100)
    p.add_argument('--sheet'); p.set_defaults(fn=cmd_detail)
    p = sp.add_parser('vstrip'); p.add_argument('region'); p.add_argument('vid'); p.add_argument('--n', type=int, default=10); p.set_defaults(fn=cmd_vstrip)
    p = sp.add_parser('export'); p.add_argument('region'); p.set_defaults(fn=cmd_export)
    a = ap.parse_args(); a.fn(a)


if __name__ == '__main__':
    main()
