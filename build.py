#!/usr/bin/env python3
"""Сборка серии отчётов по регионам России.
Запуск: python build.py
Тексты регионов лежат в src/<код>-<имя>.html, общие стили — series.css, скрипт — series.js.
Список регионов, отметок и ссылок — в переменной D ниже.
"""
import os, html, shutil, re

ROOT = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(ROOT, 'series.css'), encoding='utf-8').read()
JS = open(os.path.join(ROOT, 'series.js'), encoding='utf-8').read()
MAPJS = open(os.path.join(ROOT, 'map.js'), encoding='utf-8').read()
FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;800'
         '&family=Golos+Text:wght@400;500;600&family=Oswald:wght@500;600&display=swap">')
VK = 'https://vk.ru/@moscowserega-russia-'
SERIES_TITLE = 'Россия: регион за регионом'   # рабочее название серии, меняется здесь
SITE = 'https://ssveretennikov.github.io/russia/'   # адрес сайта; от него считаются ссылки для пересылки
INDEX_DESC = 'Цель: побывать в каждом регионе России хотя бы раз. Отчёты по регионам, по федеральным округам.'
SITE_NAME = 'Россия: регион за регионом'
SHOW_COUNTS = False   # счётчики «посещено / всего» по округам; включить, когда будут готовы все отчёты

# (код, название, столица, отметка v/h/n, [(подпись, slug)]) ; slug = хвост ссылки ВК
D = [
 ('ЦФО', 'Центральный федеральный округ', [
  ('31','Белгородская область','Белгород','n',[]),
  ('32','Брянская область','Брянск','n',[]),
  ('33','Владимирская область','Владимир','h',[('', '33')]),
  ('36','Воронежская область','Воронеж','h',[('', '36')]),
  ('37','Ивановская область','Иваново','v',[('', '37')]),
  ('40','Калужская область','Калуга','v',[('', '40')]),
  ('44','Костромская область','Кострома','v',[('', '44')]),
  ('46','Курская область','Курск','v',[('', '46')]),
  ('48','Липецкая область','Липецк','v',[('', '48')]),
  ('50','Московская область','Подольск','v',[('', '50')]),
  ('57','Орловская область','Орёл','v',[('', '57')]),
  ('62','Рязанская область','Рязань','v',[('', '62')]),
  ('67','Смоленская область','Смоленск','v',[('', '67')]),
  ('68','Тамбовская область','Тамбов','h',[('', '68')]),
  ('69','Тверская область','Тверь','v',[('', '69')]),
  ('71','Тульская область','Тула','v',[('', '71')]),
  ('76','Ярославская область','Ярославль','h',[('', '76')]),
  ('77','Москва','город федерального значения','h',[('', '77-1')]),
 ]),
 ('СЗФО', 'Северо-Западный федеральный округ', [
  ('10','Республика Карелия','Петрозаводск','v',[('', '10'),('Рускеала, водопады','10-2')]),
  ('11','Республика Коми','Сыктывкар','v',[('', '11')]),
  ('29','Архангельская область','Архангельск','h',[('', '29')]),
  ('35','Вологодская область','Вологда','h',[('', '35')]),
  ('39','Калининградская область','Калининград','h',[('', '39-1'),('2','39-2'),('3','39-3'),('4','39-4'),('5','39-5'),('6','39-6'),('7','39-7')]),
  ('47','Ленинградская область','Гатчина','v',[('', '47-2'),('Выборг','47-1')]),
  ('51','Мурманская область','Мурманск','v',[('', '51')]),
  ('53','Новгородская область','Великий Новгород','v',[('', '53')]),
  ('60','Псковская область','Псков','v',[('', '60')]),
  ('78','Санкт-Петербург','город федерального значения','h',[('', '78-1'),('часть 2','78-2'),('часть 3','78-3'),('часть 4','78-4')]),
  ('83','Ненецкий автономный округ','Нарьян-Мар','v',[('', '83')]),
 ]),
 ('ЮФО', 'Южный федеральный округ', [
  ('1','Республика Адыгея','Майкоп','h',[('', '1')]),
  ('8','Республика Калмыкия','Элиста','v',[('', '8')]),
  ('23','Краснодарский край','Краснодар','v',[('', '23')]),
  ('30','Астраханская область','Астрахань','v',[('', '30')]),
  ('34','Волгоградская область','Волгоград','v',[('', '34')]),
  ('61','Ростовская область','Ростов-на-Дону','h',[('', '61')]),
  ('82','Республика Крым','Симферополь','h',[('', '82')]),
  ('92','Севастополь','город федерального значения','v',[('', '92')]),
 ]),
 ('СКФО', 'Северо-Кавказский федеральный округ', [
  ('5','Республика Дагестан','Махачкала','h',[('', '5')]),
  ('6','Республика Ингушетия','Магас','h',[('', '6')]),
  ('7','Кабардино-Балкария','Нальчик','v',[('', '7-2'),('Эльбрус','7')]),
  ('9','Карачаево-Черкесия','Черкесск','v',[('', '9')]),
  ('15','Северная Осетия — Алания','Владикавказ','v',[('', '15')]),
  ('20','Чеченская Республика','Грозный · код 95','v',[('', '20')]),
  ('26','Ставропольский край','Ставрополь','h',[('', '26'),('Пятигорск','26-2')]),
 ]),
 ('ПФО', 'Приволжский федеральный округ', [
  ('2','Республика Башкортостан','Уфа','v',[('', '2')]),
  ('12','Республика Марий Эл','Йошкар-Ола','h',[('', '12')]),
  ('13','Республика Мордовия','Саранск','v',[('', '13')]),
  ('16','Республика Татарстан','Казань','v',[('', '16')]),
  ('18','Удмуртская Республика','Ижевск','v',[('', '18')]),
  ('21','Чувашская Республика','Чебоксары','h',[('', '21')]),
  ('43','Кировская область','Киров','v',[('', '43')]),
  ('52','Нижегородская область','Нижний Новгород','h',[('', '52')]),
  ('56','Оренбургская область','Оренбург','v',[('', '56')]),
  ('58','Пензенская область','Пенза','v',[('', '58')]),
  ('59','Пермский край','Пермь','v',[('', '59')]),
  ('63','Самарская область','Самара','h',[('', '63')]),
  ('64','Саратовская область','Саратов','v',[('', '64')]),
  ('73','Ульяновская область','Ульяновск','v',[('', '73')]),
 ]),
 ('УрФО', 'Уральский федеральный округ', [
  ('45','Курганская область','Курган','v',[('', '45')]),
  ('66','Свердловская область','Екатеринбург','v',[('', '66')]),
  ('72','Тюменская область','Тюмень','v',[('', '72'),('Тобольск','72-2')]),
  ('74','Челябинская область','Челябинск','v',[('', '74')]),
  ('86','Ханты-Мансийский АО — Югра','Ханты-Мансийск','h',[('', '86')]),
  ('89','Ямало-Ненецкий АО','Салехард','v',[('', '89')]),
 ]),
 ('СФО', 'Сибирский федеральный округ', [
  ('4','Республика Алтай','Горно-Алтайск','h',[('', '4')]),
  ('17','Республика Тыва','Кызыл','h',[('', '17')]),
  ('19','Республика Хакасия','Абакан','h',[('', '19')]),
  ('22','Алтайский край','Барнаул','v',[('', '22')]),
  ('24','Красноярский край','Красноярск','h',[('', '24')]),
  ('38','Иркутская область','Иркутск','v',[('', '38-1'),('часть 2','38-2')]),
  ('42','Кемеровская область','Кемерово','v',[('', '42')]),
  ('54','Новосибирская область','Новосибирск','v',[('', '54'),('часть 2','54-2')]),
  ('55','Омская область','Омск','h',[('', '55')]),
  ('70','Томская область','Томск','v',[('', '70')]),
 ]),
 ('ДВФО', 'Дальневосточный федеральный округ', [
  ('3','Республика Бурятия','Улан-Удэ','v',[('', '3')]),
  ('14','Республика Саха (Якутия)','Якутск','v',[('', '14')]),
  ('25','Приморский край','Владивосток','h',[('', '25')]),
  ('27','Хабаровский край','Хабаровск','v',[('', '27')]),
  ('28','Амурская область','Благовещенск','v',[('', '28')]),
  ('41','Камчатский край','Петропавловск-Камчатский','v',[('', '41')]),
  ('49','Магаданская область','Магадан','h',[('', 'LOCAL:49-magadan/index.html')]),
  ('65','Сахалинская область','Южно-Сахалинск','h',[('', '65')]),
  ('75','Забайкальский край','Чита','v',[('', '75')]),
  ('79','Еврейская автономная область','Биробиджан','v',[('', '79')]),
  ('87','Чукотский автономный округ','Анадырь','v',[]),
 ]),
 ('', 'Пока вне федеральных округов', [
  ('80','Донецкая Народная Республика','','n',[]),
  ('81','Луганская Народная Республика','','n',[]),
  ('84','Херсонская область','','n',[]),
  ('85','Запорожская область','','n',[]),
 ]),
]
NOTE87 = 'отчёт ещё не опубликован'

def e(s): return html.escape(s, quote=True)

def href(slug):
    return slug[6:] if slug.startswith('LOCAL:') else VK + slug

def code_badge(code, link=None):
    if link:
        return f'<a class="code" href="{e(link)}" aria-label="Регион {code}">{code}</a>'
    return f'<span class="code">{code}</span>'

FOKEY = {'ЦФО': 'c', 'СЗФО': 'sz', 'ЮФО': 'yu', 'СКФО': 'sk', 'ПФО': 'p', 'УрФО': 'u', 'СФО': 's', 'ДВФО': 'dv', '': 'x'}

def load_map():
    import json
    return json.load(open(os.path.join(ROOT, 'data', 'map.json'), encoding='utf-8'))

def ru_date(iso):
    mon = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
    y, m, d = iso.split('-')
    return f'{int(d)} {mon[int(m) - 1]} {y}'

def index_body():
    total = sum(len(r) for _, _, r in D)
    assert total == 89, total
    mp = load_map()
    dates = {r['code']: r['date'] for r in mp['regions']}
    import json
    trans = json.load(open(os.path.join(ROOT, 'data', 'transport.json'), encoding='utf-8'))   # код -> car/bus/plane/train/other
    order = {c: i for i, c in enumerate(sorted(dates, key=lambda c: (dates[c], int(c))))}      # порядок для анимации
    info = {}                                    # код -> (ключ округа, посещён, ссылка на отчёт)
    for short, full, regs in D:
        for code, name, cap, mark, links in regs:
            info[code] = (FOKEY[short], mark != 'n', href(links[0][1]) if links else None, bool(links) and links[0][1].startswith('LOCAL:'))
    visited = {c for c, v in info.items() if v[1]}
    assert visited == set(dates), (visited ^ set(dates))   # список D и карта должны совпадать
    years = sorted({d[:4] for d in dates.values()})
    # ---- карта ----
    paths = []
    for r in mp['regions']:
        fo, _, link, local = info[r['code']]
        cls = 'r' + (' rep' if local else '') + (' tiny' if r['tiny'] else '')
        label = e(f"{r['code']} · {r['name']}")
        paths.append(f'<path class="{cls}" data-code="{r["code"]}" data-fo="{fo}" data-year="{r["date"][:4]}" d="{r["d"]}" tabindex="0" role="link" aria-label="{label}"/>')
    chips_fo = '<button type="button" class="chip" data-k="fo" data-v="" aria-pressed="true">Все</button>' + ''.join(
        f'<button type="button" class="chip" data-k="fo" data-v="{FOKEY[s]}" aria-pressed="false" title="{e(f)}">{s}</button>' for s, f, _ in D if s)
    chips_y = '<button type="button" class="chip" data-k="year" data-v="" aria-pressed="true">Все годы</button>' + ''.join(
        f'<button type="button" class="chip" data-k="year" data-v="{y}" aria-pressed="false">{y}</button>' for y in years)
    out = [f'''<div class="page ix-page">
<header class="ix-head">
  <div class="ix-kicker">Сергей Веретенников · отчёты о поездках</div>
  <h1>{e(SERIES_TITLE)}</h1>
  <div class="ix-intro">
    <p>Цель простая: побывать в каждом регионе страны хотя бы раз. Минимум — столица региона, дальше как получится.</p>
    <p>Нажмите на регион на карте или выберите его из списка ниже, чтобы открыть отчёт.</p>
  </div>
</header>
<section class="mapbox" aria-label="Карта посещённых регионов">
  <div class="filters">
    <div class="chips" role="group" aria-label="Федеральный округ">{chips_fo}</div>
    <div class="chips" role="group" aria-label="Год поездки">{chips_y}</div>
  </div>
  <svg class="rumap" viewBox="0 0 {mp['w']} {mp['h']}" role="group" aria-label="Карта России, посещённые регионы">
{chr(10).join(paths)}
  </svg>
  <div class="anim"><button type="button" class="play" id="play">▶ Показать путь</button><span class="adate" id="adate" aria-live="polite"></span></div>
  <div class="mcard" id="mcard" aria-live="polite"><p class="mhint">Наведите на регион или нажмите на него.</p></div>
  <ul class="legend"><li><i class="k-v"></i>Побывал</li><li><i class="k-r"></i>Есть отчёт на этом сайте</li></ul>
  <p class="mnote">На карте только посещённые регионы. Остальные пока не нарисованы: они ещё впереди.</p>
</section>
''']
    for short, full, regs in D:
        got = sum(1 for x in regs if x[3] != 'n')
        title = f'{short} · {full}' if short else full
        count = f'<span>{got} / {len(regs)}</span>' if SHOW_COUNTS else ''
        out.append(f'<section class="fo" data-fo="{FOKEY[short]}"><div class="fo-h"><h2>{e(title)}</h2>{count}</div><ul class="regs">')
        for code, name, cap, mark, links in regs:
            main = href(links[0][1]) if links else None
            local = bool(links) and links[0][1].startswith('LOCAL:')
            cls = 'reg' + (' none' if mark == 'n' else '') + (' new' if local else '')
            nm = f'<a href="{e(main)}">{e(name)}</a>' if main else f'<span class="nm">{e(name)}</span>'
            if mark == 'h': nm += ' <span class="hrt">❤</span>'
            if local: nm += '<span class="tag">новый формат</span>'
            sub = [e(cap)] if cap else []
            for lab, slug in links[1:]:
                sub.append(f'<a href="{e(href(slug))}">{e(lab)}</a>')
            if code == '87': sub.append(NOTE87)
            if mark == 'n': sub.append('впереди')
            small = f'<small>{" · ".join(sub)}</small>' if sub else ''
            d = dates.get(code)
            attrs = f' data-code="{code}" data-fo="{FOKEY[short]}"' + (f' data-date="{ru_date(d)}" data-year="{d[:4]}" data-tr="{trans[code]}" data-n="{order[code]}"' if d else '')
            out.append(f'<li class="{cls}"{attrs}>{code_badge(code, main)}<div class="reg-t"><div>{nm}</div>{small}</div></li>')
        out.append('</ul></section>')
    out.append('''<footer class="ix-foot">
  <p>Старые отчёты пока открываются во ВКонтакте. Новые выходят в формате, как у Магаданской области.</p>
</footer>
</div>''')
    return '\n'.join(out)

def region_body(code, prev=None, nxt=None):
    """prev / nxt — соседи ПО МАРШРУТУ ПОЕЗДКИ: (код, название, ссылка, подпись) или None."""
    src = open(os.path.join(ROOT, 'src', f'{code}.html'), encoding='utf-8').read()
    top = ('<nav class="topbar"><a href="../index.html">← Все регионы</a>'
           '<button class="draft-toggle" type="button" id="draftToggle" hidden>Пометки</button></nav>')
    def pl(x, cls):
        if not x:
            return '<a class="%s" href="../index.html"><span>Все регионы</span></a>' % cls
        c, name, link, label = x
        txt = f'<span><small>{e(label)}</small>{e(name)}</span>'
        b = code_badge(c)
        return f'<a class="{cls}" href="{e(link)}">' + (b + txt if cls == 'prev' else txt + b) + '</a>'
    pager = '<nav class="pager" aria-label="Соседние регионы по маршруту">' + pl(prev, 'prev') + pl(nxt, 'next') + '</nav>'
    return f'<div class="page">\n{top}\n{src}\n{pager}\n</div>'

def meta_tags(title, desc, path, image):
    """Ссылки для пересылки (Open Graph) и значок. path — адрес страницы от корня сайта: '' или '49-magadan/'."""
    url = SITE + path
    img = SITE + image
    t = [
        f'<meta name="description" content="{e(desc)}">',
        f'<link rel="canonical" href="{e(url)}">',
        f'<link rel="icon" href="{SITE}favicon.png" type="image/png">',
        f'<link rel="apple-touch-icon" href="{SITE}apple-touch-icon.png">',
        '<meta property="og:type" content="article">' if path else '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{e(SITE_NAME)}">',
        f'<meta property="og:locale" content="ru_RU">',
        f'<meta property="og:title" content="{e(title)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{e(img)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(title)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{e(img)}">',
    ]
    return '\n'.join(t)

def doc(title, body, depth, inline, reg_color=None, meta=''):
    up = '../' * depth
    style = f'<style>\n{CSS}\n</style>' if inline else f'<link rel="stylesheet" href="{up}series.css">'
    script = f'<script>\n{JS}\n</script>' if inline else f'<script src="{up}series.js"></script>'
    extra = f'<style>{reg_color}</style>' if reg_color else ''
    if 'ix-page' in body:                      # главная: карта и фильтры
        script += f'\n<script>\n{MAPJS}\n</script>' if inline else f'\n<script src="{up}map.js"></script>'
    return (f'<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{e(title)}</title>\n{meta}\n{FONTS}\n{style}\n{extra}\n</head>\n<body>\n{body}\n{script}\n</body>\n</html>\n')

def fragment(title, body):
    """Главная страница артефакта: без doctype/html/head/body."""
    return f'<title>{e(title)}</title>\n{FONTS}\n<style>\n{CSS}\n</style>\n{body}\n<script>\n{JS}\n</script>\n<script>\n{MAPJS}\n</script>\n'

# Страницы регионов в новом формате. Чтобы добавить регион:
#   1) положить текст в src/<slug>.html, медиа — в <slug>/media/ (tools/media.py export);
#   2) добавить запись сюда; 3) в списке D выше заменить ссылку региона на 'LOCAL:<slug>/index.html'.
# prev / next — соседи по маршруту поездки: (код, название, ссылка, подпись) или None.
# color — цвет региона (CSS-переменные --reg и --reg-ink для светлой темы); None = охра по умолчанию.
PAGES = [
    dict(slug='49-magadan', title='49 · Магаданская область',
         prev=('41', 'Камчатский край', VK + '41', 'Раньше по маршруту'), next=None, color=None),
]

def region_style(color):
    return f':root{{--reg:{color[0]};--reg-ink:{color[1]}}}' if color else None

def write_service_files():
    """404.html, sitemap.xml, robots.txt. На странице 404 пути абсолютные: она открывается по любому адресу."""
    base = '/' + SITE.split('/', 3)[3]
    page = (f'<div class="page"><div class="lost">'
            f'<span class="code">404</span><h1>Такой страницы нет</h1>'
            f'<p>Адрес мог устареть или в нём опечатка. Отчёты по регионам собраны на главной.</p>'
            f'<p><a href="{base}">← Все регионы</a></p></div></div>')
    h = doc('Страница не найдена', page, 0, False, None, f'<link rel="icon" href="{base}favicon.png" type="image/png">\n<meta name="robots" content="noindex">')
    h = h.replace('href="series.css"', f'href="{base}series.css"').replace('src="series.js"', f'src="{base}series.js"')
    open(os.path.join(ROOT, '404.html'), 'w', encoding='utf-8').write(h)
    urls = [SITE] + [SITE + pg['slug'] + '/' for pg in PAGES]
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n')

def build(artifact=False):
    """Без аргументов собирает страницы на месте: index.html и <slug>/index.html рядом со скриптом.
    С ключом --artifact дополнительно кладёт в _artifact/ вариант со вшитыми стилями (для предпросмотра)."""
    ix = index_body()
    if artifact:
        os.makedirs(os.path.join(ROOT, '_artifact'), exist_ok=True)
        open(os.path.join(ROOT, '_artifact', 'page.html'), 'w', encoding='utf-8').write(fragment(SERIES_TITLE, ix))
    open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(
        doc(SERIES_TITLE, ix, 0, False, None, meta_tags(SERIES_TITLE, INDEX_DESC, '', 'og.jpg')))
    for pg in PAGES:
        body = region_body(pg['slug'], pg['prev'], pg['next'])
        src = open(os.path.join(ROOT, 'src', pg['slug'] + '.html'), encoding='utf-8').read()
        m = re.search(r'<p class="hook">(.*?)</p>', src, re.S)
        desc = re.sub(r'<.*?>', '', m.group(1)).strip() if m else INDEX_DESC
        pg_meta = meta_tags(pg['title'] + ' · ' + SITE_NAME, desc, pg['slug'] + '/', pg['slug'] + '/og.jpg')
        os.makedirs(os.path.join(ROOT, pg['slug']), exist_ok=True)
        open(os.path.join(ROOT, pg['slug'], 'index.html'), 'w', encoding='utf-8').write(
            doc(pg['title'], body, 1, False, region_style(pg['color']), pg_meta))
        if artifact:
            out = os.path.join(ROOT, '_artifact', pg['slug']); os.makedirs(out, exist_ok=True)
            open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(
                doc(pg['title'], body, 1, True, region_style(pg['color'])))
        print('готово:', pg['slug'] + '/index.html')
    write_service_files()
    print('готово: index.html')

if __name__ == '__main__':
    import sys
    build('--artifact' in sys.argv)
