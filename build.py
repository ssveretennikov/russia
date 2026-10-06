#!/usr/bin/env python3
"""Сборка серии отчётов по регионам России.
Запуск: python build.py
Тексты регионов лежат в src/<код>-<имя>.html, общие стили — series.css, скрипт — series.js.
Список регионов, отметок и ссылок — в переменной D ниже.
"""
import os, html, shutil, re, json

ROOT = os.path.dirname(os.path.abspath(__file__))
CSS = open(os.path.join(ROOT, 'series.css'), encoding='utf-8').read()
JS = open(os.path.join(ROOT, 'series.js'), encoding='utf-8').read()
MAPJS = open(os.path.join(ROOT, 'map.js'), encoding='utf-8').read()
import hashlib
# метка версии в ссылках на общие файлы: GitHub Pages разрешает браузеру держать их в кэше 10 минут,
# а с новой меткой после выкладки браузер берёт новый файл сразу
VER = {n: hashlib.md5(t.encode('utf-8')).hexdigest()[:8] for n, t in (('css', CSS), ('js', JS), ('map', MAPJS))}
# Шрифты — в fonts/ на сайте, правила @font-face в series.css. Здесь только предзагрузка двух файлов, нужных
# с первого экрана (кириллица текста и заголовков): браузер начнёт качать их, не дожидаясь разбора стилей.
# Латиница тоже нужна с первого экрана: цифры кодов, дат и чисел лежат в латинском наборе; Oswald — подписи шапки.
# Пять файлов, около 150 КБ, — те же, что страница всё равно скачает, только раньше.
def fonts(up):
    return ''.join(f'<link rel="preload" href="{up}fonts/{f}.woff2" as="font" type="font/woff2" crossorigin>'
                   for f in ('unbounded-cyrillic', 'unbounded-latin', 'golos-text-cyrillic', 'golos-text-latin', 'oswald-cyrillic'))
SERIES_TITLE = 'Россия: регион за регионом'   # рабочее название серии, меняется здесь
SITE = 'https://ssveretennikov.github.io/russia/'   # адрес сайта; от него считаются ссылки для пересылки
# Ролики лежат на отдельном сайте (репозиторий russia-video): GitHub Pages даёт 1 ГБ на сайт, а видео одно весит почти столько.
# В src/<slug>.html адрес ролика по-прежнему пишется как media/имя.mp4; при сборке он заменяется на адрес ниже.
# python build.py --local-video — проверка до выкладки: рядом с каждой страницей пишется index.local.html (в git не идёт),
# где ролики берутся из папки russia-video. Сами страницы сайта (index.html) этот ключ не трогает: адрес ../russia-video/
# на сайте не существует, и закоммиченная с ним страница осталась бы без роликов.
VIDEO_SITE = 'https://ssveretennikov.github.io/russia-video/'
VIDEO_BASE = VIDEO_SITE
VIDEO_USED = []      # (slug, имя.mp4) — все ролики, на которые сослались страницы; сверяется с папкой russia-video в конце сборки
INDEX_DESC ='Цель: побывать в каждом регионе России хотя бы раз. Отчёты по регионам, по федеральным округам.'
SITE_NAME = 'Россия: регион за регионом'
THEME_INIT = "<script>try{var t=localStorage.getItem('russia-theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>"
SHOW_COUNTS = False   # счётчики «посещено / всего» по округам; включить, когда будут готовы все отчёты

# (код, название, столица, отметка v/h/n, [(подпись, 'LOCAL:<папка>/index.html')]) ; h = понравилось (сердечко), n = ещё не был
D = [
 ('ЦФО', 'Центральный федеральный округ', [
  ('31','Белгородская область','Белгород','n',[]),
  ('32','Брянская область','Брянск','n',[]),
  ('33','Владимирская область','Владимир','h',[('', 'LOCAL:33-vladimir/index.html')]),
  ('36','Воронежская область','Воронеж','h',[('', 'LOCAL:36-voronezh/index.html')]),
  ('37','Ивановская область','Иваново','v',[('', 'LOCAL:37-ivanovo/index.html')]),
  ('40','Калужская область','Калуга','v',[('', 'LOCAL:40-kaluga/index.html')]),
  ('44','Костромская область','Кострома','v',[('', 'LOCAL:44-kostroma/index.html')]),
  ('46','Курская область','Курск','v',[('', 'LOCAL:46-kursk/index.html')]),
  ('48','Липецкая область','Липецк','v',[('', 'LOCAL:48-lipetsk/index.html')]),
  ('50','Московская область','Подольск','v',[('', 'LOCAL:50-moscow-oblast/index.html'),('2','LOCAL:50-moscow-oblast-2/index.html')]),
  ('57','Орловская область','Орёл','v',[('', 'LOCAL:57-oryol/index.html')]),
  ('62','Рязанская область','Рязань','v',[('', 'LOCAL:62-ryazan/index.html')]),
  ('67','Смоленская область','Смоленск','v',[('', 'LOCAL:67-smolensk/index.html')]),
  ('68','Тамбовская область','Тамбов','h',[('', 'LOCAL:68-tambov/index.html')]),
  ('69','Тверская область','Тверь','v',[('', 'LOCAL:69-tver/index.html')]),
  ('71','Тульская область','Тула','v',[('', 'LOCAL:71-tula/index.html')]),
  ('76','Ярославская область','Ярославль','h',[('', 'LOCAL:76-yaroslavl/index.html')]),
  ('77','Москва','город федерального значения','h',[('', 'LOCAL:77-moscow-1/index.html'),('2','LOCAL:77-moscow-2/index.html'),('3','LOCAL:77-moscow-3/index.html'),('4','LOCAL:77-moscow-4/index.html')]),
 ]),
 ('СЗФО', 'Северо-Западный федеральный округ', [
  ('10','Республика Карелия','Петрозаводск','v',[('', 'LOCAL:10-karelia/index.html')]),
  ('11','Республика Коми','Сыктывкар','v',[('', 'LOCAL:11-komi/index.html')]),
  ('29','Архангельская область','Архангельск','h',[('', 'LOCAL:29-arkhangelsk/index.html')]),
  ('35','Вологодская область','Вологда','h',[('', 'LOCAL:35-vologda/index.html')]),
  ('39','Калининградская область','Калининград','h',[('', 'LOCAL:39-kaliningrad/index.html')]),
  ('47','Ленинградская область','Гатчина','v',[('', 'LOCAL:47-leningrad/index.html')]),
  ('51','Мурманская область','Мурманск','v',[('', 'LOCAL:51-murmansk/index.html')]),
  ('53','Новгородская область','Великий Новгород','v',[('', 'LOCAL:53-novgorod/index.html')]),
  ('60','Псковская область','Псков','v',[('', 'LOCAL:60-pskov/index.html')]),
  ('78','Санкт-Петербург','город федерального значения','h',[('', 'LOCAL:78-spb/index.html'),('месяц в Питере','LOCAL:78-spb-month/index.html')]),
  ('83','Ненецкий автономный округ','Нарьян-Мар','v',[('', 'LOCAL:83-nenets/index.html')]),
 ]),
 ('ЮФО', 'Южный федеральный округ', [
  ('1','Республика Адыгея','Майкоп','h',[('', 'LOCAL:01-adygeya/index.html')]),
  ('8','Республика Калмыкия','Элиста','v',[('', 'LOCAL:08-kalmykia/index.html')]),
  ('23','Краснодарский край','Краснодар','v',[('', 'LOCAL:23-krasnodar/index.html')]),
  ('30','Астраханская область','Астрахань','v',[('', 'LOCAL:30-astrakhan/index.html')]),
  ('34','Волгоградская область','Волгоград','v',[('', 'LOCAL:34-volgograd/index.html')]),
  ('61','Ростовская область','Ростов-на-Дону','h',[('', 'LOCAL:61-rostov/index.html')]),
  ('91','Республика Крым','Симферополь','h',[('', 'LOCAL:91-krym/index.html')]),
  ('92','Севастополь','город федерального значения','v',[('', 'LOCAL:92-sevastopol/index.html')]),
 ]),
 ('СКФО', 'Северо-Кавказский федеральный округ', [
  ('5','Республика Дагестан','Махачкала','h',[('', 'LOCAL:05-dagestan/index.html')]),
  ('6','Республика Ингушетия','Магас','h',[('', 'LOCAL:06-ingushetia/index.html')]),
  ('7','Кабардино-Балкария','Нальчик','v',[('', 'LOCAL:07-kabardino-balkaria/index.html')]),
  ('9','Карачаево-Черкесия','Черкесск','v',[('', 'LOCAL:09-karachay-cherkessia/index.html')]),
  ('15','Северная Осетия — Алания','Владикавказ','v',[('', 'LOCAL:15-north-ossetia/index.html')]),
  ('20','Чеченская Республика','Грозный · код 95','v',[('', 'LOCAL:20-chechnya/index.html')]),
  ('26','Ставропольский край','Ставрополь','h',[('', 'LOCAL:26-stavropol/index.html')]),
 ]),
 ('ПФО', 'Приволжский федеральный округ', [
  ('2','Республика Башкортостан','Уфа','v',[('', 'LOCAL:02-bashkortostan/index.html')]),
  ('12','Республика Марий Эл','Йошкар-Ола','h',[('', 'LOCAL:12-mari-el/index.html')]),
  ('13','Республика Мордовия','Саранск','v',[('', 'LOCAL:13-mordovia/index.html')]),
  ('16','Республика Татарстан','Казань','v',[('', 'LOCAL:16-tatarstan/index.html')]),
  ('18','Удмуртская Республика','Ижевск','v',[('', 'LOCAL:18-udmurtia/index.html')]),
  ('21','Чувашская Республика','Чебоксары','h',[('', 'LOCAL:21-chuvashia/index.html')]),
  ('43','Кировская область','Киров','v',[('', 'LOCAL:43-kirov/index.html')]),
  ('52','Нижегородская область','Нижний Новгород','h',[('', 'LOCAL:52-nizhny-novgorod/index.html')]),
  ('56','Оренбургская область','Оренбург','v',[('', 'LOCAL:56-orenburg/index.html')]),
  ('58','Пензенская область','Пенза','v',[('', 'LOCAL:58-penza/index.html')]),
  ('59','Пермский край','Пермь','v',[('', 'LOCAL:59-perm/index.html')]),
  ('63','Самарская область','Самара','h',[('', 'LOCAL:63-samara/index.html')]),
  ('64','Саратовская область','Саратов','v',[('', 'LOCAL:64-saratov/index.html')]),
  ('73','Ульяновская область','Ульяновск','v',[('', 'LOCAL:73-ulyanovsk/index.html')]),
 ]),
 ('УрФО', 'Уральский федеральный округ', [
  ('45','Курганская область','Курган','v',[('', 'LOCAL:45-kurgan/index.html')]),
  ('66','Свердловская область','Екатеринбург','v',[('', 'LOCAL:66-sverdlovsk/index.html')]),
  ('72','Тюменская область','Тюмень','v',[('', 'LOCAL:72-tyumen/index.html'),('Тобольск','LOCAL:72-tobolsk/index.html')]),
  ('74','Челябинская область','Челябинск','v',[('', 'LOCAL:74-chelyabinsk/index.html')]),
  ('86','Ханты-Мансийский АО — Югра','Ханты-Мансийск','h',[('', 'LOCAL:86-khanty-mansi/index.html')]),
  ('89','Ямало-Ненецкий АО','Салехард','v',[('', 'LOCAL:89-yamal/index.html')]),
 ]),
 ('СФО', 'Сибирский федеральный округ', [
  ('4','Республика Алтай','Горно-Алтайск','h',[('', 'LOCAL:04-altai-republic/index.html')]),
  ('17','Республика Тыва','Кызыл','h',[('', 'LOCAL:17-tuva/index.html')]),
  ('19','Республика Хакасия','Абакан','h',[('', 'LOCAL:19-khakassia/index.html')]),
  ('22','Алтайский край','Барнаул','v',[('', 'LOCAL:22-altai-krai/index.html')]),
  ('24','Красноярский край','Красноярск','h',[('', 'LOCAL:24-krasnoyarsk/index.html')]),
  ('38','Иркутская область','Иркутск','v',[('', 'LOCAL:38-irkutsk/index.html')]),
  ('42','Кемеровская область','Кемерово','v',[('', 'LOCAL:42-kemerovo/index.html')]),
  ('54','Новосибирская область','Новосибирск','v',[('', 'LOCAL:54-novosibirsk/index.html')]),
  ('55','Омская область','Омск','h',[('', 'LOCAL:55-omsk/index.html')]),
  ('70','Томская область','Томск','v',[('', 'LOCAL:70-tomsk/index.html')]),
 ]),
 ('ДВФО', 'Дальневосточный федеральный округ', [
  ('3','Республика Бурятия','Улан-Удэ','v',[('', 'LOCAL:03-buryatia/index.html')]),
  ('14','Республика Саха (Якутия)','Якутск','v',[('', 'LOCAL:14-yakutia/index.html'),('Мирный','LOCAL:14-mirny/index.html')]),
  ('25','Приморский край','Владивосток','h',[('', 'LOCAL:25-primorye/index.html')]),
  ('27','Хабаровский край','Хабаровск','v',[('', 'LOCAL:27-khabarovsk/index.html')]),
  ('28','Амурская область','Благовещенск','v',[('', 'LOCAL:28-amur/index.html')]),
  ('41','Камчатский край','Петропавловск-Камчатский','h',[('', 'LOCAL:41-kamchatka/index.html')]),
  ('49','Магаданская область','Магадан','h',[('', 'LOCAL:49-magadan/index.html')]),
  ('65','Сахалинская область','Южно-Сахалинск','h',[('', 'LOCAL:65-sakhalin/index.html')]),
  ('75','Забайкальский край','Чита','v',[('', 'LOCAL:75-zabaykalsky/index.html')]),
  ('79','Еврейская автономная область','Биробиджан','v',[('', 'LOCAL:79-jewish-ao/index.html')]),
  ('87','Чукотский автономный округ','Анадырь','h',[('', 'LOCAL:87-chukotka/index.html')]),
 ]),
 ('', 'Пока вне федеральных округов', [
  ('80','Донецкая Народная Республика','','n',[]),
  ('81','Луганская Народная Республика','','n',[]),
  ('84','Херсонская область','','n',[]),
  ('85','Запорожская область','','n',[]),
 ]),
]

def e(s): return html.escape(s, quote=True)

def href(slug):
    # все отчёты — на сайте; ссылки во ВКонтакте убраны по решению автора 05.10.2026
    assert slug.startswith('LOCAL:'), f'ссылка не на страницу сайта: {slug}'
    return slug[6:]

def code_badge(code, link=None):
    if link:
        return f'<a class="code" href="{e(link)}" aria-label="Регион {code}">{code}</a>'
    return f'<span class="code">{code}</span>'

HOME = '77'   # Москва — дом автора, начало и конец большинства поездок; решение автора 05.10.2026

# Лента «Любимые» на главной (макет Б, 06.10.2026): шесть регионов с сердечком, с запада на восток.
# Набор и порядок — заготовка из макета, уточняет автор. У каждого должен быть card.webp (tools/thumbs.py).
FAV = ['39-kaliningrad', '91-krym', '05-dagestan', '04-altai-republic', '65-sakhalin', '41-kamchatka']

def places_of(slug):
    """Места из шапки отчёта (<div class="reg-places"> в src/<slug>.html) — для строки поиска на главной:
    так находятся Тобольск, Мирный, Куршская коса, а не только название региона и столица."""
    f = os.path.join(ROOT, 'src', slug + '.html')
    if not os.path.exists(f): return ''
    m = re.search(r'<div class="reg-places"[^>]*>(.*?)</div>', open(f, encoding='utf-8').read(), re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).replace('·', ' ') if m else ''

ALIASES = {'78': 'питер спб петербург', '77': 'мск'}   # разговорные имена, которых нет ни в названии, ни в столице

def hook_of(slug):
    """Крючок отчёта (<p class="hook"> в src/<slug>.html) как чистый текст: для строки списка и карточки ленты."""
    f = os.path.join(ROOT, 'src', slug + '.html')
    if not os.path.exists(f): return ''
    m = re.search(r'<p class="hook"[^>]*>(.*?)</p>', open(f, encoding='utf-8').read(), re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))).strip() if m else ''

FOKEY = {'ЦФО': 'c', 'СЗФО': 'sz', 'ЮФО': 'yu', 'СКФО': 'sk', 'ПФО': 'p', 'УрФО': 'u', 'СФО': 's', 'ДВФО': 'dv', '': 'x'}

# значки кнопок хронологии: рисунок, а не символ — символы ⏮ ▶ ⏭ телефоны подменяют цветными эмодзи
def _icon(name, d):
    return f'<svg class="i-{name}" viewBox="0 0 24 24" aria-hidden="true"><path d="{d}"/></svg>'
ICON = {'prev': _icon('prev', 'M6 5h2v14H6zM20 5v14L9 12z'), 'next': _icon('next', 'M16 5h2v14h-2zM4 5v14l11-7z'),
        'play': _icon('play', 'M8 5v14l11-7z'), 'pause': _icon('pause', 'M7 5h4v14H7zM13 5h4v14h-4z')}

def load_map():
    import json
    return json.load(open(os.path.join(ROOT, 'data', 'map.json'), encoding='utf-8'))

def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11: return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14: return few
    return many

def month_year(iso):
    mon = ['январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь']
    y, m, _ = iso.split('-')
    return f'{mon[int(m) - 1]} {y}'

def find_key(s):
    """Строка для поиска на главной: строчные, ё = е — «орел» находит «Орёл»."""
    return s.lower().replace('ё', 'е')

def ru_date(iso):
    mon = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']
    y, m, d = iso.split('-')
    return f'{int(d)} {mon[int(m) - 1]} {y}'

def index_body():
    total = sum(len(r) for _, _, r in D)
    assert total == 89, total
    mp = load_map()
    dates = {r['code']: r['date'] for r in mp['regions'] if r['date']}
    import json
    trans = json.load(open(os.path.join(ROOT, 'data', 'transport.json'), encoding='utf-8'))   # код -> car/bus/plane/train/other
    order = {c: i for i, c in enumerate(sorted(dates, key=lambda c: (dates[c], int(c))))}      # порядок для анимации
    info = {}                                    # код -> (ключ округа, посещён, ссылка на отчёт)
    for short, full, regs in D:
        for code, name, cap, mark, links in regs:
            info[code] = (FOKEY[short], mark != 'n', href(links[0][1]) if links else None, bool(links) and links[0][1].startswith('LOCAL:'))
    visited = {c for c, v in info.items() if v[1]}
    assert visited == set(dates), (visited ^ set(dates))   # список D и карта должны совпадать
    # Дом не поездка: дата у Москвы в данных условная, поэтому в годах, хронологии и «последнем новом регионе»
    # она не участвует, а на карте горит с первой даты — отсюда поездки начинаются.
    trips = {c: d for c, d in dates.items() if c != HOME}
    years = sorted({d[:4] for d in trips.values()})
    # Цвет на карте — по «возрасту» года первой поездки: 0 — последний год, 3 — третий с конца и раньше.
    # Привязка к возрасту, а не к самому году: новый год сам станет самым заметным, стили править не нужно.
    def age(y): return min(3, len(years) - 1 - years.index(y))
    # Легенда годов — она же фильтр по году: отдельные кнопки годов повторяли её второй раз.
    legend = (''.join(f'<li><button type="button" class="ychip" data-k="year" data-v="{y}" aria-pressed="false"><i class="k-a{age(y)}"></i>{y}</button></li>' for y in years)
              + '<li class="k-ahead"><i class="k-n"></i>Ещё впереди</li>')
    # Шаги «Пути по годам» — поездки из data/trips.json: [начало, конец, [коды]]. Код — число в начале slug;
    # Москвы и Подмосковья там нет намеренно (дом), они горят с первого шага.
    codes = {r['code'] for r in mp['regions']}
    tsteps = []
    for t in sorted(TRIPS, key=lambda t: t['start']):
        cs = []
        for sl in t['regions']:
            c = str(int(sl.split('-')[0]))
            assert c in codes, sl
            if c not in cs: cs.append(c)
        tsteps.append([t['start'], t['end'], cs])
    tsteps_json = e(json.dumps(tsteps, ensure_ascii=False, separators=(',', ':')))
    # ---- прогресс для шапки: считается из тех же дат, что и карта, руками не правится ----
    names = {code: name for _, _, regs in D for code, name, *_ in regs}
    first_iso, last_iso = min(trips.values()), max(trips.values())
    last = [names[c] for c in sorted(trips, key=int) if trips[c] == last_iso]
    last_txt = last[0] + (f' и ещё {len(last) - 1}' if len(last) > 1 else '')
    since = ru_date(first_iso).split(' ', 1)[1]          # «февраля 2022» — для «с февраля 2022»
    left = total - len(visited)
    stats = f'''<div class="ix-stats">
    <p class="ix-big"><b>{len(visited)}</b> из {total} <span>регионов</span></p>
    <div class="ix-bar" role="progressbar" aria-label="Посещено регионов" aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="{len(visited)}"><i style="width:{len(visited) / total * 100:.1f}%"></i></div>
    <dl class="ix-facts">
      <div><dt>В пути</dt><dd>с {since}</dd></div>
      <div><dt>Последний новый регион</dt><dd>{ru_date(last_iso)} · {e(last_txt)}</dd></div>
      <div><dt>Впереди</dt><dd>{left} {plural(left, "регион", "региона", "регионов")}</dd></div>
    </dl>
  </div>'''
    # ---- карта ----
    paths = []
    for r in mp['regions']:
        fo, _, link, local = info[r['code']]
        cls = 'r' + (' no' if not r['date'] else '') + (' tiny' if r['tiny'] else '')
        label = e(f"{r['code']} · {r['name']}" + ('' if r['date'] else ' (впереди)'))
        yr = f' data-year="{trips[r["code"]][:4]}" data-age="{age(trips[r["code"]][:4])}"' if r['code'] in trips else ''
        paths.append(f'<path class="{cls}" data-code="{r["code"]}" data-fo="{fo}"{yr} d="{r["d"]}" tabindex="0" role="{"link" if link else "img"}" aria-label="{label}"/>')
    chips_fo = '<button type="button" class="chip" data-k="fo" data-v="" aria-pressed="true">Все</button>' + ''.join(
        f'<button type="button" class="chip" data-k="fo" data-v="{FOKEY[s]}" aria-pressed="false" title="{e(f)}">{s}</button>' for s, f, _ in D if s)
    out = [f'''<div class="page ix-page">
<header class="ix-head">
  <div class="ix-top"><div class="ix-kicker">Сергей Веретенников · отчёты о поездках</div><button class="theme-btn" type="button" id="themeBtn" hidden>Тема</button></div>
  <h1>{e(SERIES_TITLE)}</h1>
  <div class="ix-intro">
    <p>Цель простая: побывать в каждом регионе страны хотя бы раз. Минимум — столица региона, дальше как получится.</p>
    <p class="ix-how">Нажмите на регион на карте или выберите его из списка ниже, чтобы открыть отчёт.</p>
  </div>
  {stats}
</header>
<section class="mapbox" id="karta" aria-label="Карта посещённых регионов" data-trips="{tsteps_json}">
  <div class="filters">
    <div class="chips" role="group" aria-label="Федеральный округ">{chips_fo}</div>
  </div>
  <div class="mapwrap">
  <svg class="rumap" viewBox="0 0 {mp['w']} {mp['h']}" role="group" aria-label="Карта России, посещённые регионы">
<defs><pattern id="hatch" class="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7"/><line x1="0" y1="0" x2="0" y2="7"/></pattern></defs>
{chr(10).join(paths)}
  </svg>
  <p class="mapdate" id="mapdate" aria-hidden="true" hidden></p>
  </div>
  <div class="mapbar">
    <ul class="legend" role="group" aria-label="Год первой поездки — нажмите, чтобы оставить только его">{legend}</ul>
    <div class="mapbtns"><button type="button" class="zoom" id="zoom" aria-pressed="false">Европейская часть</button></div>
  </div>
  <div class="mcard" id="mcard" aria-live="polite"><p class="mhint"><span class="h-mouse">Наведите на регион или нажмите на него.</span><span class="h-touch">Нажмите на регион — появится ссылка на отчёт.</span></p></div>
  <div class="tl" aria-label="Хронология поездок">
    <div class="tl-ctl"><button type="button" id="tprev" aria-label="Предыдущая поездка">{ICON['prev']}</button><button type="button" class="play" id="play" aria-label="Посмотреть маршрут: воспроизвести">{ICON['play']}{ICON['pause']}<span>Посмотреть маршрут</span></button><button type="button" id="tnext" aria-label="Следующая поездка">{ICON['next']}</button></div>
    <div class="tl-track"><input type="range" id="track" min="0" value="0" aria-label="Поездка на временной шкале"><div class="ruler" id="ruler" aria-hidden="true"></div></div>
    <div class="tl-read" aria-live="polite"><strong id="tdate">Все поездки</strong><span id="tnote"></span><span class="tl-chain" id="tchain" hidden></span></div>
    <button type="button" class="tl-all" id="tall" hidden>Показать весь период</button>
  </div>
</section>
''']
    def reg_li(short, code, name, cap, mark, links):
        main = href(links[0][1]) if links else None
        cls = 'reg' + (' none' if mark == 'n' else '')
        nm = f'<a href="{e(main)}">{e(name)}</a>' if main else f'<span class="nm">{e(name)}</span>'
        # сердечко читателю не объясняется (решение автора): без всплывающей подсказки; &nbsp; — чтобы не отрывалось от названия
        if mark == 'h': nm += '&nbsp;<span class="hrt" role="img" aria-label="понравилось">❤</span>'
        d = trips.get(code)
        sub = [e(cap)] if cap else []
        if d: sub.append(month_year(d))
        if code == HOME: sub.append('дом')
        for lab, slug in links[1:]:   # вторые части отчёта: «2» → «часть 2»
            # название второй страницы из PAGES («Центр и вода») без кода и региона; нет его — «часть N»
            t = next((pg['title'] for pg in PAGES if pg['slug'] == href(slug).split('/')[0]), '')
            sname = t.rsplit(' · ', 1)[1] if t.count(' · ') >= 2 else ('часть ' + lab if lab.isdigit() else lab)
            sub.append(f'<a href="{e(href(slug))}">{e(sname)}</a>')
        small = f'<small>{" · ".join(sub)}</small>' if sub else ''
        # строка крючка из отчёта (у региона с несколькими страницами — с первой), серым с многоточием
        hook = main and hook_of(main.split('/')[0])
        hk = f'<span class="hk">{e(hook)}</span>' if hook else ''
        q = ' '.join([name, cap, ALIASES.get(code, '')] + [places_of(href(sl).split('/')[0]) for _, sl in links]
                     + [lab for lab, _ in links[1:] if not lab.isdigit()])
        attrs = f' data-code="{code}" data-fo="{FOKEY[short]}" data-cap="{e(cap)}" data-q="{e(find_key(q))}"'
        if d: attrs += f' data-date="{ru_date(d)}" data-year="{d[:4]}" data-iso="{d}" data-tr="{trans[code]}"'
        if code == HOME: attrs += f' data-home="1" data-iso="{first_iso}"'   # в хронологии горит с первой даты
        # миниатюра — tools/thumbs.py; грузится по мере прокрутки, карточка на карте берёт её же; нажимается — ведёт на отчёт
        th = main and main.split('/')[0] + '/thumb.webp'
        img = (f'<a class="th-a" href="{e(main)}" tabindex="-1" aria-hidden="true"><img class="th" src="{th}" alt="" width="360" height="270" loading="lazy" decoding="async"></a>'
               if th and os.path.exists(os.path.join(ROOT, th)) else '')
        return f'<li class="{cls}"{attrs}>{code_badge(code, main)}<div class="reg-t"><div>{nm}</div>{small}{hk}</div>{img}</li>'

    # подписи «❤ — понравилось» у поиска нет: сердечко читателю не объясняется (решение автора)
    out.append('''<div class="ix-find">
  <input type="search" id="find" placeholder="Найти регион или город" aria-label="Найти регион или город" autocomplete="off">
  <a class="ix-trips" href="trips/index.html">Все поездки →</a>
</div>
<p class="ix-none" id="none" hidden>Ничего не нашлось.</p>''')
    out.append(fav_section(trips))
    for short, full, regs in D:
        been = [r for r in regs if r[3] != 'n']
        if not been: continue
        title = f'{short} · {full}' if short else full
        count = f'<span>{len(been)} / {len(regs)}</span>' if SHOW_COUNTS else ''
        out.append(f'<section class="fo" data-fo="{FOKEY[short]}"><div class="fo-h"><h2>{e(title)}</h2>{count}</div><ul class="regs">')
        out += [reg_li(short, *r) for r in been]
        out.append('</ul></section>')
    # шесть оставшихся — отдельным блоком в конце (макет Б): серыми строками внутри округов они терялись,
    # а наверху отодвигали посещённые регионы от карты
    ahead = [(s, r) for s, _, regs in D for r in regs if r[3] == 'n']
    out.append(f'<section class="fo ahead" data-fo="ahead"><div class="fo-h"><h2>Впереди · {len(ahead)} '
               f'{plural(len(ahead), "регион", "региона", "регионов")}</h2></div><ul class="regs">')
    out += [reg_li(s, *r) for s, r in ahead]
    out.append('</ul></section>')
    out.append('<a class="totop" id="totop" href="#karta" hidden>↑ К карте</a>\n</div>')
    return '\n'.join(out)

def fav_section(trips):
    """Лента «Любимые» (макет Б): карточки регионов из FAV — card.webp, код, название, столица · дата, крючок, ссылка.
    Скрипт map.js прячет её, пока работает поиск, фильтр или хронология."""
    rows = {}
    for short, full, regs in D:
        for code, name, cap, mark, links in regs:
            if links: rows[href(links[0][1]).split('/')[0]] = (code, name, cap, mark)
    cards = []
    for slug in FAV:
        code, name, cap, mark = rows[slug]
        assert mark == 'h', f'{slug}: в ленте «Любимые» только регионы с сердечком'
        img = slug + '/card.webp'
        assert os.path.exists(os.path.join(ROOT, img)), f'нет {img}: запустите python tools/thumbs.py'
        meta = [e(cap)] if cap else []
        if code in trips: meta.append(month_year(trips[code]))
        cards.append(
            f'<li class="fc"><a href="{slug}/index.html">'
            f'<span class="fc-ph"><img src="{img}" alt="" width="800" height="600" decoding="async">'
            f'<span class="code">{code}</span></span>'
            f'<span class="fc-t"><strong class="fc-nm">{e(name)}</strong>'
            f'<span class="fc-meta">{" · ".join(meta)}</span>'
            f'<span class="fc-hook">{e(hook_of(slug))}</span>'
            f'<span class="fc-go">Открыть отчёт →</span></span></a></li>')
    arrow = lambda d: f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{d}"/></svg>'
    return ('<section class="fav" id="fav" aria-labelledby="fav-h">\n'
            '  <div class="fav-h"><h2 id="fav-h">Любимые</h2><div class="fav-nav" id="favNav">'
            f'<button type="button" id="favPrev" aria-label="Предыдущие">{arrow("M15 5l-7 7 7 7")}</button>'
            f'<button type="button" id="favNext" aria-label="Следующие">{arrow("M9 5l7 7-7 7")}</button>'
            '</div></div>\n  <ul class="fav-row" id="favRow">\n' + '\n'.join(cards) + '\n  </ul>\n</section>')

# ---- Карта дня и профиль высоты: строятся из GPS снимков (regions/<slug>/index.tsv) и отбора (selection.tsv).
#   В тексте страницы: <!--daymap: 44.608,40.098 Майкоп; 44.237,40.157 Смотровая--> и <!--profile-->.
#   Точки отобранных фото — ссылки на <figure id="P016">. Если данных нет, метки просто убираются.
import math, csv

def _gps_rows(slug):
    f = os.path.join(ROOT, 'regions', slug, 'index.tsv')
    if not os.path.exists(f): return [], {}
    rows = []
    for r in csv.DictReader(open(f, encoding='utf-8'), delimiter='\t'):
        if r['lat'] and r['lon'] and r['taken']:
            rows.append(dict(id=r['id'], t=r['taken'], lat=float(r['lat']), lon=float(r['lon']), alt=float(r['alt'] or 0)))
    rows.sort(key=lambda r: r['t'])
    sel = {}
    sf = os.path.join(ROOT, 'regions', slug, 'selection.tsv')
    if os.path.exists(sf):
        for line in open(sf, encoding='utf-8'):
            c = line.rstrip('\n').split('\t')
            if len(c) > 1 and c[1].startswith('P'): sel[c[1]] = c[0]
    return rows, sel

def _tmin(t):
    return int(t[11:13]) * 60 + int(t[14:16])


def _km(la1, lo1, la2, lo2):
    k = math.cos(math.radians((la1 + la2) / 2))
    return 111.2 * math.hypot(la1 - la2, (lo1 - lo2) * k)

def daymap_svg(slug, labels, ids=()):
    """Карта мест дня: только названные места из метки, пронумерованные и соединённые линией по порядку.
    Снимки архива не рисуются — каждый относится к ближайшему месту (не дальше 15 км) и даёт число «N фото».
    Названия — под картой списком со ссылкой на первый кадр места на странице: на телефоне подписи в SVG
    становились мельче 7 px, а сотни ссылок внутри картинки мешали читалкам."""
    if not labels: return ''
    rows, sel = _gps_rows(slug)
    n = len(labels)
    counts = [0] * n; first = [None] * n
    for r in rows:   # строки уже по времени: первый попавший кадр — самый ранний
        d = [_km(r['lat'], r['lon'], la, lo) for la, lo, _ in labels]
        i = min(range(n), key=d.__getitem__)
        if d[i] > 15: continue
        counts[i] += 1
        if first[i] is None and r['id'] in ids: first[i] = r['id']
    W, pad = 360, 26   # ширина как у колонки текста на телефоне: номер 13 px читается без увеличения
    lat0 = sum(l[0] for l in labels) / n; k = math.cos(math.radians(lat0))
    xs = [lo * k for _, lo, _ in labels]; ys = [la for la, _, _ in labels]
    dx, dy = max(max(xs) - min(xs), 1e-4), max(max(ys) - min(ys), 1e-4)
    iw = W - 2 * pad; ih = max(120, min(300, iw * dy / dx)); H = int(ih + 2 * pad + 18)
    span = max(dx, dy * iw / ih)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    P = lambda la, lo: (pad + iw * (0.5 + (lo * k - cx) / span), pad + ih * (0.5 - (la - cy) / span * iw / ih))
    true = [P(la, lo) for la, lo, _ in labels]
    # близкие места раздвигаются, к настоящему положению ведёт тонкая линия
    R, gap = 11, 25
    pos = [list(p) for p in true]
    for _ in range(200):
        moved = False
        for a in range(n):
            for b in range(a + 1, n):
                vx, vy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]; d = math.hypot(vx, vy)
                if d < gap:
                    if d < 1e-6: vx, vy, d = 1.0, 0.3 * (b - a), math.hypot(1.0, 0.3 * (b - a))
                    s = (gap - d) / 2 / d
                    pos[a][0] -= vx * s; pos[a][1] -= vy * s; pos[b][0] += vx * s; pos[b][1] += vy * s; moved = True
        for p in pos:
            p[0] = min(max(p[0], R + 2), W - R - 2); p[1] = min(max(p[1], R + 2), H - 28)
        if not moved: break
    for a in range(n):
        for b in range(a + 1, n):
            if math.hypot(pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]) < 2 * R + 1:
                print(f'ВНИМАНИЕ: {slug}: номера {a + 1} и {b + 1} на карте мест накладываются')
    name = next((nm for _, _, regs in D for _, nm, _, _, links in regs for _, sl in links
                 if href(sl).split('/')[0] == slug), '')
    out = [f'<svg class="daymap-svg" viewBox="0 0 {W} {H}" role="img" aria-label="Карта мест{(" — " + e(name)) if name else ""}: '
           f'{n} {plural(n, "место", "места", "мест")} по порядку, названия — списком под картой">']
    for i in range(n - 1):   # переезд дальше 50 км — пунктир: между точками не шли, а ехали
        far = _km(labels[i][0], labels[i][1], labels[i + 1][0], labels[i + 1][1]) > 50
        (x1, y1), (x2, y2) = true[i], true[i + 1]
        out.append(f'<line class="dm-route{" dm-far" if far else ""}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    for i in range(n):
        (tx, ty), (x, y) = true[i], pos[i]
        if math.hypot(tx - x, ty - y) > 1:
            out.append(f'<line class="dm-lead" x1="{tx:.1f}" y1="{ty:.1f}" x2="{x:.1f}" y2="{y:.1f}"/><circle class="dm-dot" cx="{tx:.1f}" cy="{ty:.1f}" r="2.5"/>')
    for i in range(n):
        x, y = pos[i]
        out.append(f'<g class="dm-num"><circle cx="{x:.1f}" cy="{y:.1f}" r="{R}"/><text x="{x:.1f}" y="{y + 4.5:.1f}" text-anchor="middle">{i + 1}</text></g>')
    # линейка: круглое число километров не длиннее четверти ширины
    km_px = iw / (span * 111.2)
    step = next((v for v in (1000, 500, 200, 100, 50, 20, 10, 5, 2, 1, .5, .2, .1) if v * km_px <= iw / 4), .1)
    L = step * km_px; lab = f'{step:g} км' if step >= 1 else f'{int(step * 1000)} м'
    out.append(f'<g class="dm-scale"><path d="M{pad},{H - 14} v-5 h{L:.1f} v5"/><text x="{pad + L + 6:.1f}" y="{H - 13}">{lab}</text></g>')
    out.append('</svg>')
    li = []
    for i, (_, _, nm) in enumerate(labels):
        t = f'<a href="#{first[i]}">{e(nm)}</a>' if first[i] else e(nm)
        c = f' <span class="dm-n">· {counts[i]} фото</span>' if counts[i] else ''
        li.append(f'<li>{t}{c}</li>')
    return '\n'.join(out) + '\n<ol class="dm-list">' + ''.join(li) + '</ol>'


def profile_svg(slug):
    rows, sel = _gps_rows(slug)
    rows = [r for r in rows if r['alt'] > 0]
    if len(rows) < 2: return ''
    W, H, pl, pb, pt = 640, 220, 60, 26, 14
    t0 = min(_tmin(r['t']) for r in rows) - 15; t1 = max(_tmin(r['t']) for r in rows) + 15
    a0 = max(0, min(r['alt'] for r in rows) - 50); a1 = max(r['alt'] for r in rows) + 50
    def P(r):
        return (pl + (W - pl - 10) * (_tmin(r['t']) - t0) / (t1 - t0), pt + (H - pt - pb) * (1 - (r['alt'] - a0) / (a1 - a0)))
    pts = ' '.join(f'{x:.1f},{y:.1f}' for x, y in map(P, rows))
    out = [f'<svg class="profile-svg" viewBox="0 0 {W} {H}" role="img" aria-label="Высота по времени дня">']
    for h in range((t0 // 60) + 1, (t1 // 60) + 1):
        x = pl + (W - pl - 10) * (h * 60 - t0) / (t1 - t0)
        out.append(f'<line class="pf-grid" x1="{x:.1f}" y1="{pt}" x2="{x:.1f}" y2="{H - pb}"/><text class="pf-ax" x="{x:.1f}" y="{H - 8}" text-anchor="middle">{h}:00</text>')
    for a in (a0 + 50, a1 - 50):
        y = pt + (H - pt - pb) * (1 - (a - a0) / (a1 - a0))
        out.append(f'<text class="pf-ax" x="{pl - 6}" y="{y + 4:.1f}" text-anchor="end">{int(round(a, -1))} м</text>')
    out.append(f'<polyline class="pf-line" points="{pts}"/>')
    for r in rows:
        if r['id'] in sel:
            x, y = P(r)
            out.append(f'<a href="#{r["id"]}" class="dm-pt"><circle cx="{x:.1f}" cy="{y:.1f}" r="5"><title>{r["t"][11:16]} · {int(r["alt"])} м</title></circle></a>')
    out.append('</svg>')
    return '\n'.join(out)

# Ширина кадра на экране по виду фигуры — по раскладке series.css: медиа до 74rem (1184 px) на компьютере
# и до 62rem между 640 и 900 px, текст 42rem, ряд — половина; на телефоне всё во всю ширину.
SIZES = {'wide': '(max-width: 640px) 100vw, (max-width: 1200px) 90vw, 1184px',
         'col': '(max-width: 640px) 100vw, 672px',
         'row': '(max-width: 640px) 100vw, (max-width: 1200px) 45vw, 592px',
         'hero': '100vw'}

def mobile_srcset(slug, fig, inner):
    """Если рядом с media/x.webp лежит копия для телефона x.m.webp (tools/media.py mobile), картинке
    добавляются srcset и sizes: телефон берёт копию в 1080 px, компьютер — оригинал. src остаётся оригиналом —
    его открывает лайтбокс."""
    cls = re.search(r'class="([^"]*)"', fig)
    cls = cls.group(1).split() if cls else []
    kind = 'hero' if 'hero-ph' in cls else 'wide' if 'wide' in cls else 'col' if ('mid' in cls or 'tall' in cls) else 'row'
    def one(m):
        tag = m.group(0)
        s = re.search(r'src="media/([^"]+)\.webp"', tag); w = re.search(r'width="(\d+)"', tag)
        if not s or not w or 'srcset=' in tag: return tag
        if not os.path.exists(os.path.join(ROOT, slug, 'media', s.group(1) + '.m.webp')): return tag
        return tag.replace(s.group(0), s.group(0) + f' srcset="media/{s.group(1)}.m.webp 1080w, media/{s.group(1)}.webp {w.group(1)}w" sizes="{SIZES[kind]}"', 1)
    return re.sub(r'<img [^>]*>', one, inner)

def inject_data(slug, src):
    """Подставляет карту дня, профиль высоты и реальные размеры картинок из regions/<slug>/media.tsv."""
    def dm(m):
        labels = []
        for part in (m.group(1) or '').split(';'):
            part = part.strip()
            mm = re.match(r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)\s+(.+)', part)
            if mm: labels.append((float(mm[1]), float(mm[2]), mm[3].strip()))
        return daymap_svg(slug, labels, ids)
    ids = set(re.findall(r'<figure[^>]* id="(P[0-9]+)"', src))
    src = src.replace('<figure class="wide daymap">', '<figure class="daymap">')   # в ширину колонки текста
    src = re.sub(r'<!--daymap:?(.*?)-->', dm, src, flags=re.S)
    src = re.sub(r'<!--profile-->', lambda m: profile_svg(slug), src)
    mt = os.path.join(ROOT, 'regions', slug, 'media.tsv')
    if os.path.exists(mt):
        dims = {r['name']: (r['w'], r['h']) for r in csv.DictReader(open(mt, encoding='utf-8'), delimiter='\t')}
        def fix(m):
            name = m.group(2).rsplit('.', 1)[0]
            if name in dims:
                w, h = dims[name]; return f'{m.group(1)}width="{w}" height="{h}"'
            return m.group(0)
        src = re.sub(r'(src="media/([^"]+)" )width="\d+" height="\d+"', fix, src)
    src = re.sub(r'(<figure\b[^>]*>)(.*?)(</figure>)', lambda m: m.group(1) + mobile_srcset(slug, m.group(1), m.group(2)) + m.group(3), src, flags=re.S)
    # ролик — с отдельного сайта; обложка (poster) остаётся в media/ рядом со страницей
    def video(m):
        VIDEO_USED.append((slug, m.group(1)))
        return f'src="{VIDEO_BASE}{slug}/{m.group(1)}"'
    src = re.sub(r'src="media/([^"]+\.mp4)"', video, src)
    # ролик и его обложка не качаются, пока до них не докрутили: preload="none", а poster подставляет
    # series.js у края окна (атрибут poster браузер грузит сразу, даже у ролика в конце страницы)
    src = re.sub(r'<video [^>]*>', lambda m: m.group(0).replace('preload="metadata"', 'preload="none"').replace(' poster="', ' data-poster="'), src)
    return src

def cover_head(src):
    """Шапка-обложка (решение автора 06.10.2026, вариант А): главное фото первым во всю ширину, код и название
    поверх нижней части кадра, остальное — под кадром. Исходники src/*.html остаются «анкетой» (код, название,
    места, крючок, паспорт, маршрут, фото) — их 90 и они содержание, а не вёрстка; перестановка делается здесь.
    Если шапка исходника устроена иначе и какой-то части нет — ошибка сборки, а не молча кривая страница."""
    m = re.search(r'<header class="reg-head">(.*?)</header>', src, re.S)
    if not m: raise ValueError('в исходнике нет <header class="reg-head">')
    h = m.group(1)
    def part(rx, name):
        mm = re.search(rx, h, re.S)
        if not mm: raise ValueError(f'в шапке исходника нет части «{name}»')
        return mm
    code = part(r'<span class="code"[^>]*>.*?</span>', 'код').group(0)
    h1 = part(r'<h1>(.*?)</h1>', 'название')
    places = part(r'<div class="reg-places">.*?</div>', 'места').group(0)
    hook = part(r'<p class="hook">.*?</p>', 'крючок').group(0)
    passport = part(r'<dl class="passport">.*?</dl>', 'паспорт').group(0)
    route = part(r'<ol class="route"[^>]*>.*?</ol>', 'маршрут').group(0)
    fig = part(r'<figure class="hero-ph"([^>]*)>\s*<div class="ph"><img ([^>]*)></div>\s*(<figcaption>.*?</figcaption>)\s*</figure>', 'главный кадр')
    fig_attrs, img_attrs, caption = fig.groups()
    w = re.search(r'width="(\d+)"', img_attrs); hh = re.search(r'height="(\d+)"', img_attrs)
    portrait = bool(w and hh and int(w.group(1)) < int(hh.group(1)))
    img_src = re.search(r'src="([^"]+)"', img_attrs).group(1)
    ss = ''.join(re.findall(r' (?:srcset|sizes)="[^"]*"', ' ' + img_attrs))   # размытой копии — тот же файл, что главному кадру
    # вертикальный кадр в широкую полосу не режем: он целиком, а поля по бокам — его же размытая копия.
    # Копия — отдельная картинка, а не url() в стилях: адрес в style="" считался бы от series.css в корне сайта
    ph = (f'<div class="ph"><img class="cover-bg" src="{img_src}"{ss} alt="" aria-hidden="true">' if portrait else '<div class="ph">')
    # на узком телефоне кегль названия подбирается так, чтобы самое длинное слово встало в строку целиком
    longest = max(len(wd) for wd in re.sub(r'<[^>]+>', '', h1.group(1)).split()) if h1.group(1).strip() else 1
    head = (f'<header class="reg-head cover-head">\n'
            f'  <figure class="hero-ph cover{" portrait" if portrait else ""}"{fig_attrs}>\n'
            f'    {ph}<img fetchpriority="high" {img_attrs}></div>\n'
            f'    <div class="reg-id" style="--nw:{longest}">\n      {code}\n      <h1>{h1.group(1)}</h1>\n    </div>\n'
            f'    {caption}\n  </figure>\n'
            f'  <div class="under">\n    {places}\n    {hook}\n    {passport}\n    {route}\n  </div>\n'
            f'</header>')
    return src[:m.start()] + head + src[m.end():]

def _page_code(slug):
    return slug.split('-')[0].lstrip('0')

def _page_name(slug):
    """Название страницы из PAGES без кода: «77 · Москва · Центр и вода» -> «Москва · Центр и вода»."""
    t = next((pg['title'] for pg in PAGES if pg['slug'] == slug), slug)
    return t.split(' · ', 1)[1] if ' · ' in t else t

def _ref(slug, label):
    return (_page_code(slug), _page_name(slug), f'../{slug}/index.html', label)

def read_next(slug, prev, nxt):
    """Соседи внизу страницы. Порядок: prev/next из PAGES (расставлял автор) -> соседи в той же поездке
    из data/trips.json -> «Следующий отчёт» (ближайший по дате первой поездки в регион, у Москвы и Подмосковья —
    по коду: их в trips.json нет намеренно). Пустое место слева занимает «Все регионы» — только слева,
    чтобы на странице не стояли две одинаковые ссылки подряд."""
    slugs = [pg['slug'] for pg in PAGES]
    if not (prev and nxt):
        for t in TRIPS:
            rs = [r for r in t['regions'] if r in slugs]
            if slug in rs and len(rs) > 1:
                i = rs.index(slug)
                if not prev and i > 0: prev = _ref(rs[i - 1], 'Раньше по маршруту')
                if not nxt and i < len(rs) - 1: nxt = _ref(rs[i + 1], 'Дальше по маршруту')
                break
    aria = 'Соседние регионы по маршруту'
    if not nxt:
        dates = {r['code']: r.get('date') or '' for r in load_map()['regions']}
        code = _page_code(slug)
        if code in ('77', '50') or not dates.get(code):
            order = sorted(slugs, key=lambda s: (int(_page_code(s)), s))
        else:
            order = sorted([s for s in slugs if dates.get(_page_code(s)) and _page_code(s) not in ('77', '50')],
                           key=lambda s: (dates[_page_code(s)], s))
        i = order.index(slug)
        taken = {prev and prev[2], f'../{slug}/index.html'}
        for k in range(1, len(order)):
            cand = order[(i + k) % len(order)]
            if f'../{cand}/index.html' not in taken:
                nxt = _ref(cand, 'Следующий отчёт'); break
        aria = 'Читать дальше'
    return prev, nxt, aria

def _tail_block(body):
    """Если тело главы кончается блоком оценки (div.verdict) или счёта (dl.bill) — (тело без него, блок).
    Берётся только хвост: ценник посреди главы (Камчатка, «Лава с ценником») остаётся на месте."""
    s = body.rstrip()
    if s.endswith('</dl>'):
        i = s.rfind('<dl class="bill"')
        if i >= 0 and '</dl>' not in s[i:-5]: return s[:i], s[i:]
    if s.endswith('</div>'):
        i = s.rfind('<div class="verdict"')
        if i >= 0:
            depth, k = 0, i                       # в оценке вложенный div — ищем её парный </div>
            for m in re.finditer(r'<div\b|</div>', s[i:]):
                depth += 1 if m.group(0) == '<div' else -1
                if depth == 0: k = i + m.end(); break
            if k == len(s): return s[:i], s[i:]
    return None

def _plain(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', x)).strip()

def chapters_and_final(src):
    """Оглавление и финал страницы региона (этап 2). Исходники src/*.html не трогаем: здесь у каждого h2
    появляется якорь g1, g2…, оценка и «Счёт по региону» из хвоста последней главы уходят в отдельный
    section.sec.final, а после вводки (первой секции) встаёт список глав. Возвращает (страница, липкая строка)."""
    secs = list(re.finditer(r'<section class="sec">(.*?)</section>', src, re.S))
    if not secs: return src, ''
    last = secs[-1]
    body, moved = last.group(1), []
    while True:
        t = _tail_block(body)
        if not t: break
        body, blk = t; moved.insert(0, blk)
    final = ''
    if moved:
        final = ('\n\n<section class="sec final" id="final" aria-labelledby="final-h">\n'
                 '  <div class="day final-h" id="final-h">Итого</div>\n  ' + '\n  '.join(moved) + '\n</section>')
        src = src[:last.start()] + f'<section class="sec">{body}\n</section>' + final + src[last.end():]
    n = 0
    def anchor(m):
        nonlocal n
        n += 1
        return f'<h2 id="g{n}">'
    src = re.sub(r'<h2>', anchor, src)
    items = []
    for sm in re.finditer(r'<section class="sec">(.*?)</section>', src, re.S):
        h = re.search(r'<h2 id="(g\d+)">(.*?)</h2>', sm.group(1), re.S)
        if not h: continue
        d = re.search(r'<div class="day">(.*?)</div>', sm.group(1), re.S)
        day = f'<span class="toc-d">{_plain(d.group(1))}</span>' if d else ''
        items.append(f'<li><a href="#{h.group(1)}">{day}<span class="toc-t">{_plain(h.group(2))}</span></a></li>')
    if final:
        items.append('<li><a href="#final"><span class="toc-t">Итого</span></a></li>')
    if len(items) < 2: return src, ''
    toc = ('<section class="sec toc-sec"><nav class="toc" id="toc" aria-label="Главы">\n'
           '  <div class="toc-h">Главы</div>\n  <ol>\n    ' + '\n    '.join(items) + '\n  </ol>\n</nav></section>')
    first = re.search(r'<section class="sec">.*?</section>', src, re.S)
    if 'class="lead"' in first.group(0) and '<h2' not in first.group(0):
        src = src[:first.end()] + '\n\n' + toc + src[first.end():]
    else:
        src = src[:first.start()] + toc + '\n\n' + src[first.start():]
    # строка для телефона: название текущей главы (ссылка к оглавлению) и «наверх»; показывает series.js
    bar = ('<div class="chap-bar" id="chapBar" hidden><a class="cb-t" href="#toc"></a>'
           '<a class="cb-up" href="#top">Наверх ↑</a></div>')
    return src, bar

def region_body(code, prev=None, nxt=None):
    """prev / nxt — соседи ПО МАРШРУТУ ПОЕЗДКИ: (код, название, ссылка, подпись) или None."""
    src = cover_head(inject_data(code, open(os.path.join(ROOT, 'src', f'{code}.html'), encoding='utf-8').read()))
    src, bar = chapters_and_final(src)
    top = ('<nav class="topbar"><a href="../index.html">← Все регионы</a>'
           '<div class="topbar-r"><button class="theme-btn" type="button" id="themeBtn" hidden>Тема</button>'
           '<button class="draft-toggle" type="button" id="draftToggle" hidden>Пометки</button></div></nav>')
    prev, nxt, aria = read_next(code, prev, nxt)
    def pl(x, cls):
        if not x:
            return '<a class="%s" href="../index.html"><span>Все регионы</span></a>' % cls
        c, name, link, label = x
        txt = f'<span><small>{e(label)}</small>{e(name)}</span>'
        b = code_badge(c)
        return f'<a class="{cls}" href="{e(link)}">' + (b + txt if cls == 'prev' else txt + b) + '</a>'
    pager = f'<nav class="pager" aria-label="{aria}">' + pl(prev, 'prev') + pl(nxt, 'next') + '</nav>'
    return f'<div class="page page-cover">\n{top}\n{bar}\n{src}\n{pager}\n</div>'

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

def footer(up, home):
    """Общий подвал. На главной название без ссылки (она и есть главная). Контактов автор не давал —
    если появятся, им место строкой после .ft-who."""
    name = f'<span class="ft-name">{e(SERIES_TITLE)}</span>' if home else f'<a class="ft-name" href="{up}index.html">{e(SERIES_TITLE)}</a>'
    return (f'<footer class="site-foot{" ft-home" if home else ""}" role="contentinfo"><div class="ft-in">'
            f'<div class="ft-t">{name}<p class="ft-who">Сергей Веретенников · отчёты о поездках</p>'
            f'<p class="ft-aim">Цель — побывать в каждом регионе России хотя бы раз.</p>'
            f'<p class="ft-nav"><a href="{up}trips/index.html">Поездки</a> · <a href="{up}about/index.html">О проекте</a></p></div>'
            f'<a class="ft-top" href="#top">Наверх ↑</a></div></footer>')

def doc(title, body, depth, inline, reg_color=None, meta=''):
    up = '../' * depth
    if 'class="lost"' not in body:   # на 404 подвала нет: её пути относительные, а открывается она по любому адресу
        body += '\n' + footer(up, 'ix-page' in body)
    style = f'<style>\n{CSS}\n</style>' if inline else f'<link rel="stylesheet" href="{up}series.css?v={VER["css"]}">'
    script = f'<script>\n{JS}\n</script>' if inline else f'<script src="{up}series.js?v={VER["js"]}"></script>'
    extra = f'<style>{reg_color}</style>' if reg_color else ''
    # цвет адресной строки телефона: на главной — синяя шапка, на страницах регионов — фон страницы
    light, dark = ('#1F6FE5', '#2A63C4') if 'ix-page' in body else ('#F1F2EE', '#101315')
    meta += (f'\n<meta name="theme-color" content="{light}" media="(prefers-color-scheme: light)">'
             f'\n<meta name="theme-color" content="{dark}" media="(prefers-color-scheme: dark)">')
    # главный кадр региона браузер начинает качать сразу, не дожидаясь стилей: он — самое крупное на первом экране
    hero = re.search(r'<img fetchpriority="high" ([^>]*)>', body)
    if hero:
        a = dict(re.findall(r'\b(src|srcset|sizes)="([^"]*)"', hero.group(1)))
        meta += (f'\n<link rel="preload" as="image" href="{a["src"]}" fetchpriority="high"'
                 + (f' imagesrcset="{a["srcset"]}" imagesizes="{a["sizes"]}"' if 'srcset' in a else '') + '>')
    if 'ix-page' in body:                      # главная: карта и фильтры
        script += f'\n<script>\n{MAPJS}\n</script>' if inline else f'\n<script src="{up}map.js?v={VER["map"]}"></script>'
    return (f'<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<title>{e(title)}</title>\n{meta}\n{THEME_INIT}\n{fonts(up)}\n{style}\n{extra}\n</head>\n<body id="top">\n{body}\n{script}\n</body>\n</html>\n')

def fragment(title, body):
    """Главная страница артефакта: без doctype/html/head/body."""
    return f'<title>{e(title)}</title>\n<style>\n{CSS}\n</style>\n{body}\n<script>\n{JS}\n</script>\n<script>\n{MAPJS}\n</script>\n'

# Страницы регионов в новом формате. Чтобы добавить регион:
#   1) положить текст в src/<slug>.html, медиа — в <slug>/media/ (tools/media.py export);
#   2) добавить запись сюда; 3) в списке D выше заменить ссылку региона на 'LOCAL:<slug>/index.html';
#   4) python tools/og.py <slug> и python tools/thumbs.py — обложка для ссылок и миниатюра для главной.
# prev / next — соседи по маршруту поездки: (код, название, ссылка, подпись) или None.
# og — кадр для обложки ссылки (tools/og.py), если главный кадр для неё не годится, например вертикальный; по умолчанию hero.
# color — цвет региона (CSS-переменные --reg и --reg-ink для светлой темы); None = охра по умолчанию.
PAGES = [
    dict(slug='13-mordovia', title='13 · Республика Мордовия', prev=None, next=None, color=None),
    dict(slug='14-yakutia', title='14 · Республика Саха (Якутия)', prev=None, next=('14', 'Мирный', '../14-mirny/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='14-mirny', title='14 · Мирный', prev=('14', 'Республика Саха (Якутия)', '../14-yakutia/index.html', 'Раньше по маршруту'), next=None, color=None),
    dict(slug='15-north-ossetia', title='15 · Северная Осетия — Алания', prev=None, next=None, color=None),
    dict(slug='16-tatarstan', title='16 · Республика Татарстан', prev=None, next=None, color=None),
    dict(slug='17-tuva', title='17 · Республика Тыва', prev=None, next=None, color=None),
    dict(slug='18-udmurtia', title='18 · Удмуртская Республика', prev=None, next=None, color=None),
    dict(slug='19-khakassia', title='19 · Республика Хакасия', prev=None, next=None, color=None),
    dict(slug='20-chechnya', title='20 · Чеченская Республика', prev=None, next=None, color=None),
    dict(slug='21-chuvashia', title='21 · Чувашская Республика', prev=None, next=None, color=None),
    dict(slug='23-krasnodar', title='23 · Краснодарский край',
         prev=None, next=('1', 'Республика Адыгея', '../01-adygeya/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='24-krasnoyarsk', title='24 · Красноярский край', prev=None, next=None, color=None),
    dict(slug='25-primorye', title='25 · Приморский край', prev=None, next=None, color=None),
    dict(slug='26-stavropol', title='26 · Ставропольский край', prev=None, next=None, color=None),
    dict(slug='27-khabarovsk', title='27 · Хабаровский край', prev=None, next=None, color=None),
    dict(slug='28-amur', title='28 · Амурская область', prev=None, next=None, color=None),
    dict(slug='29-arkhangelsk', title='29 · Архангельская область', prev=None, next=None, color=None),
    dict(slug='30-astrakhan', title='30 · Астраханская область', prev=None, next=None, color=None),
    dict(slug='33-vladimir', title='33 · Владимирская область', prev=None, next=None, color=None),
    dict(slug='34-volgograd', title='34 · Волгоградская область', prev=None, next=None, color=None),
    dict(slug='35-vologda', title='35 · Вологодская область', prev=None, next=None, color=None),
    dict(slug='36-voronezh', title='36 · Воронежская область', prev=None, next=None, color=None),
    dict(slug='37-ivanovo', title='37 · Ивановская область', prev=None, next=None, color=None),
    dict(slug='38-irkutsk', title='38 · Иркутская область', prev=None, next=None, color=None),
    dict(slug='39-kaliningrad', title='39 · Калининградская область', prev=None, next=None, color=None),
    dict(slug='40-kaluga', title='40 · Калужская область', prev=None, next=None, color=None),
    dict(slug='42-kemerovo', title='42 · Кемеровская область', prev=None, next=None, color=None),
    dict(slug='43-kirov', title='43 · Кировская область', prev=None, next=None, color=None),
    dict(slug='44-kostroma', title='44 · Костромская область', prev=None, next=None, color=None),
    dict(slug='45-kurgan', title='45 · Курганская область', prev=None, next=None, color=None),
    dict(slug='46-kursk', title='46 · Курская область', prev=None, next=None, color=None),
    dict(slug='47-leningrad', title='47 · Ленинградская область', prev=None, next=None, color=None),
    dict(slug='48-lipetsk', title='48 · Липецкая область', prev=None, next=None, color=None),
    dict(slug='51-murmansk', title='51 · Мурманская область', prev=None, next=None, color=None),
    dict(slug='52-nizhny-novgorod', title='52 · Нижегородская область', prev=None, next=None, color=None),
    dict(slug='53-novgorod', title='53 · Новгородская область', prev=None, next=None, color=None),
    dict(slug='54-novosibirsk', title='54 · Новосибирская область', prev=None, next=None, color=None),
    dict(slug='55-omsk', title='55 · Омская область', prev=None, next=None, color=None),
    dict(slug='56-orenburg', title='56 · Оренбургская область', prev=None, next=None, color=None),
    dict(slug='57-oryol', title='57 · Орловская область', prev=None, next=None, color=None),
    dict(slug='58-penza', title='58 · Пензенская область', prev=None, next=None, color=None),
    dict(slug='59-perm', title='59 · Пермский край', prev=None, next=None, color=None),
    dict(slug='60-pskov', title='60 · Псковская область', prev=None, next=None, color=None),
    dict(slug='61-rostov', title='61 · Ростовская область', prev=None, next=None, color=None),
    dict(slug='62-ryazan', title='62 · Рязанская область', prev=None, next=None, color=None),
    dict(slug='63-samara', title='63 · Самарская область', prev=None, next=None, color=None),
    dict(slug='64-saratov', title='64 · Саратовская область', prev=None, next=None, color=None),
    dict(slug='65-sakhalin', title='65 · Сахалинская область', prev=None, next=None, color=None),
    dict(slug='66-sverdlovsk', title='66 · Свердловская область', prev=None, next=None, color=None),
    dict(slug='67-smolensk', title='67 · Смоленская область', prev=None, next=None, color=None),
    dict(slug='68-tambov', title='68 · Тамбовская область', prev=None, next=None, color=None),
    dict(slug='69-tver', title='69 · Тверская область', prev=None, next=None, color=None),
    dict(slug='70-tomsk', title='70 · Томская область', prev=None, next=None, color=None),
    dict(slug='71-tula', title='71 · Тульская область', prev=None, next=None, color=None),
    dict(slug='72-tyumen', title='72 · Тюменская область', prev=None, next=('72', 'Тобольск', '../72-tobolsk/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='72-tobolsk', title='72 · Тобольск', prev=('72', 'Тюменская область', '../72-tyumen/index.html', 'Раньше по маршруту'), next=None, color=None),
    dict(slug='73-ulyanovsk', title='73 · Ульяновская область', prev=None, next=None, color=None),
    dict(slug='74-chelyabinsk', title='74 · Челябинская область', prev=None, next=None, color=None),
    dict(slug='75-zabaykalsky', title='75 · Забайкальский край', prev=None, next=None, color=None),
    dict(slug='76-yaroslavl', title='76 · Ярославская область', prev=None, next=None, color=None),
    dict(slug='78-spb', title='78 · Санкт-Петербург · три дня в июне', prev=None, next=('78', 'Месяц в Питере', '../78-spb-month/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='78-spb-month', title='78 · Санкт-Петербург · месяц в Питере', prev=('78', 'Три дня в июне', '../78-spb/index.html', 'Раньше по маршруту'), next=None, color=None),
    dict(slug='79-jewish-ao', title='79 · Еврейская автономная область', prev=None, next=None, color=None),
    dict(slug='83-nenets', title='83 · Ненецкий автономный округ', prev=None, next=None, color=None),
    dict(slug='86-khanty-mansi', title='86 · Ханты-Мансийский АО — Югра', prev=None, next=None, color=None),
    dict(slug='89-yamal', title='89 · Ямало-Ненецкий АО', prev=None, next=None, color=None),
    dict(slug='01-adygeya', title='1 · Республика Адыгея',
         prev=('23', 'Краснодарский край', '../23-krasnodar/index.html', 'Раньше по маршруту'), next=None, color=None),
    dict(slug='02-bashkortostan', title='2 · Республика Башкортостан', prev=None, next=None, color=None),
    dict(slug='03-buryatia', title='3 · Республика Бурятия', prev=None, next=None, color=None),
    dict(slug='05-dagestan', title='5 · Республика Дагестан', prev=None, next=None, color=None),
    dict(slug='06-ingushetia', title='6 · Республика Ингушетия', prev=None, next=None, color=None),
    dict(slug='07-kabardino-balkaria', title='7 · Кабардино-Балкарская Республика', prev=None, next=None, color=None),
    dict(slug='08-kalmykia', title='8 · Республика Калмыкия', prev=None, next=None, color=None),
    dict(slug='09-karachay-cherkessia', title='9 · Карачаево-Черкесия', prev=None, next=None, color=None),
    dict(slug='10-karelia', title='10 · Республика Карелия', prev=None, next=None, color=None),
    dict(slug='11-komi', title='11 · Республика Коми', prev=None, next=None, color=None),
    dict(slug='12-mari-el', title='12 · Республика Марий Эл', prev=None, next=None, color=None),
    dict(slug='50-moscow-oblast', title='50 · Московская область · Подольск',
         prev=None, next=('50', 'Московская область · парк «Патриот»', '../50-moscow-oblast-2/index.html', 'Следующая часть'), color=None),
    dict(slug='50-moscow-oblast-2', title='50 · Московская область · парк «Патриот»',
         prev=('50', 'Московская область · Подольск', '../50-moscow-oblast/index.html', 'Предыдущая часть'), next=None, color=None),
    dict(slug='77-moscow-1', title='77 · Москва · Выходные в мае 2023',
         prev=None,
         next=('77', 'Москва · Центр и вода', '../77-moscow-2/index.html', 'Следующая часть'), color=None),
    dict(slug='77-moscow-2', title='77 · Москва · Центр и вода',
         prev=('77', 'Москва · Выходные в мае 2023', '../77-moscow-1/index.html', 'Предыдущая часть'),
         next=('77', 'Москва · События', '../77-moscow-3/index.html', 'Следующая часть'), color=None),
    dict(slug='77-moscow-3', title='77 · Москва · События',
         prev=('77', 'Москва · Центр и вода', '../77-moscow-2/index.html', 'Предыдущая часть'),
         next=('77', 'Москва · «Россия» на ВДНХ и Новый год', '../77-moscow-4/index.html', 'Следующая часть'), color=None),
    dict(slug='77-moscow-4', title='77 · Москва · «Россия» на ВДНХ и Новый год',
         prev=('77', 'Москва · События', '../77-moscow-3/index.html', 'Предыдущая часть'),
         next=None, color=None),
    dict(slug='87-chukotka', title='87 · Чукотский автономный округ',
         prev=None, next=('41', 'Камчатский край', '../41-kamchatka/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='49-magadan', title='49 · Магаданская область',
         prev=('41', 'Камчатский край', '../41-kamchatka/index.html', 'Раньше по маршруту'), next=None, color=None),
    dict(slug='41-kamchatka', title='41 · Камчатский край',
         prev=('87', 'Чукотский автономный округ', '../87-chukotka/index.html', 'Раньше по маршруту'),
         next=('49', 'Магаданская область', '../49-magadan/index.html', 'Дальше по маршруту'), color=None),
    dict(slug='91-krym', title='91 · Республика Крым',
         prev=None, next=None, color=None),
    dict(slug='92-sevastopol', title='92 · Севастополь',
         prev=None,
         next=None, color=None),
    dict(slug='22-altai-krai', title='22 · Алтайский край',
         prev=None, next=('4', 'Республика Алтай', '../04-altai-republic/index.html', 'Дальше по маршруту'), color=None,
         og='media/most.webp'),
    dict(slug='04-altai-republic', title='4 · Республика Алтай',
         prev=('22', 'Алтайский край', '../22-altai-krai/index.html', 'Раньше по маршруту'), next=None, color=None),
]

TRIPS = [t for t in (json.load(open(os.path.join(ROOT, 'data', 'trips.json'), encoding='utf-8'))
         if os.path.exists(os.path.join(ROOT, 'data', 'trips.json')) else []) if t.get('regions')]   # пустая поездка = убрана автором

COLORS = json.load(open(os.path.join(ROOT, 'data', 'colors.json'), encoding='utf-8')) if os.path.exists(os.path.join(ROOT, 'data', 'colors.json')) else {}

def region_style(color, slug=None):
    """Свой цвет региона — по главному кадру (tools/regcolor.py -> data/colors.json), если в PAGES не задан явно.
    Пара на каждую тему: в светлой — тёмный цвет с белым текстом, в тёмной — светлый с тёмным текстом.
    Тёмные правила повторяют селекторы series.css, иначе её тёмная тема перебьёт цвет региона."""
    if color:
        return f':root{{--reg:{color[0]};--reg-ink:{color[1]}}}'
    c = COLORS.get(slug)
    if not c: return None
    dark = f'--reg:{c["dark"]};--reg-ink:#14100A'
    return (f':root{{--reg:{c["light"]};--reg-ink:#FFFFFF}}'
            f'@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{dark}}}}}'
            f':root[data-theme="dark"]{{{dark}}}')

# ---------- страницы «Поездки» и «О проекте» (этап 4) ----------
TRANSPORT_WORD = {'plane': 'самолётом', 'train': 'поездом', 'bus': 'автобусом', 'car': 'на машине'}   # other — без подписи: что именно, неизвестно
MONTHS = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря']

def trip_dates(a, b):
    """«19–20 февраля 2022», «24 апреля — 10 мая 2022», «30 декабря 2023 — 2 января 2024»."""
    (y1, m1, d1), (y2, m2, d2) = (tuple(int(x) for x in s.split('-')) for s in (a, b))
    if a == b: return f'{d1} {MONTHS[m1 - 1]} {y1}'
    if y1 != y2: return f'{d1} {MONTHS[m1 - 1]} {y1} — {d2} {MONTHS[m2 - 1]} {y2}'
    if m1 != m2: return f'{d1} {MONTHS[m1 - 1]} — {d2} {MONTHS[m2 - 1]} {y1}'
    return f'{d1}–{d2} {MONTHS[m1 - 1]} {y1}'

def trip_days(a, b):
    import datetime
    return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days + 1

def _top(up):
    return (f'<nav class="topbar"><a href="{up}index.html">← Все регионы</a>'
            '<div class="topbar-r"><button class="theme-btn" type="button" id="themeBtn" hidden>Тема</button></div></nav>')

def trips_body():
    """Все поездки из data/trips.json по годам. Пометка checked — внутренняя, на страницу не выводится."""
    import json
    trips = sorted(TRIPS, key=lambda t: t['start'])   # TRIPS уже без пустых поездок, убранных автором
    trans = json.load(open(os.path.join(ROOT, 'data', 'transport.json'), encoding='utf-8'))
    regs = {_page_code(s) for t in trips for s in t['regions']}   # по кодам: у Якутии две страницы (14-yakutia, 14-mirny)
    longest = max(trips, key=lambda t: (trip_days(t['start'], t['end']), t['start']))
    ld = trip_days(longest['start'], longest['end'])
    n = len(trips)
    lead = (f'{n} {plural(n, "поездка", "поездки", "поездок")} с февраля 2022 года, в них '
            f'{len(regs)} {plural(len(regs), "регион", "региона", "регионов")} — без Москвы и Подмосковья: это дом, '
            f'отсюда поездки начинаются. Самая длинная — {ld} {plural(ld, "день", "дня", "дней")}, '
            f'{trip_dates(longest["start"], longest["end"])}. Поездки — по годам, регионы в каждой — по маршруту.')
    out = ['<div class="page tr-page">', _top('../'), '<header class="tr-head"><h1>Поездки</h1>',
           f'<p class="tr-lead">{e(lead)}</p></header>']
    for y in sorted({t['start'][:4] for t in trips}):
        ts = [t for t in trips if t['start'][:4] == y]
        ry = len({_page_code(s) for t in ts for s in t['regions']})
        out.append(f'<section class="tr-year" aria-labelledby="y{y}"><div class="tr-yh"><h2 id="y{y}">{y}</h2>'
                   f'<span>{len(ts)} {plural(len(ts), "поездка", "поездки", "поездок")} · {ry} {plural(ry, "регион", "региона", "регионов")}</span></div><ol class="tr-list">')
        for t in ts:
            first = t['regions'][0]
            days, k = trip_days(t['start'], t['end']), len(t['regions'])
            how = TRANSPORT_WORD.get(trans.get(_page_code(first), ''), '')
            how = f' · <span class="tr-how">{how}</span>' if how else ''
            chain = []
            for s in t['regions']:
                c = COLORS.get(s)
                st = f' style="--c:{c["light"]};--cd:{c["dark"]}"' if c else ''
                chain.append(f'<li><a href="../{s}/index.html"{st}><span class="code">{_page_code(s)}</span>'
                             f'<small>{e(_page_name(s))}</small></a></li>')
            th = f'{first}/thumb.webp'
            img = (f'<img class="tr-th" src="../{th}" alt="" width="360" height="270" loading="lazy" decoding="async">'
                   if os.path.exists(os.path.join(ROOT, th)) else '')
            out.append(f'<li class="tr-card">{img}<div class="tr-t"><div class="tr-d">{trip_dates(t["start"], t["end"])}</div>'
                       f'<div class="tr-m">{days} {plural(days, "день", "дня", "дней")} · {k} {plural(k, "регион", "региона", "регионов")}{how}</div>'
                       f'<ol class="tr-chain" aria-label="Регионы по маршруту">{"".join(chain)}</ol></div></li>')
        out.append('</ol></section>')
    out.append('</div>')
    return '\n'.join(out), lead

ABOUT = [
    'Цель простая: побывать в каждом регионе России хотя бы раз. Минимум — столица региона, дальше как получится. '
    'Счёт идёт с февраля 2022 года, хотя поездки были и раньше.',
    'По каждому региону — отчёт в одном формате: главный кадр, несколько фактов, дни поездки с фотографиями '
    'и короткими подписями, оценка и «счёт по региону» — цифры этой поездки, серьёзные вперемешку с дурацкими. '
    'Номер у региона — это код субъекта РФ.',
    'Фотографии и видео — мои, если не подписано иначе. Цены — из чеков и ценников, время — из снимков. Чего не знаю — не пишу.',
    'Автор — Сергей Веретенников. Сайт собран из статических страниц и живёт на GitHub Pages.',
]

def about_body():
    ps = '\n'.join(f'<p>{e(p)}</p>' for p in ABOUT)
    return (f'<div class="page ab-page">\n{_top("../")}\n<article class="ab-text"><h1>О проекте</h1>\n{ps}\n'
            '<!-- Контакты: автор их пока не давал. Появятся — строкой здесь, например <p>Написать: …</p> -->\n'
            '<p class="ab-links"><a href="../index.html">Все регионы</a> · <a href="../trips/index.html">Поездки</a></p>'
            '\n</article>\n</div>'), ABOUT[0]

def write_extra_pages():
    for slug, title, fn in (('trips', 'Поездки', trips_body), ('about', 'О проекте', about_body)):
        body, desc = fn()
        full = f'{title} · {SITE_NAME}'
        os.makedirs(os.path.join(ROOT, slug), exist_ok=True)
        open(os.path.join(ROOT, slug, 'index.html'), 'w', encoding='utf-8').write(
            doc(full, body, 1, False, None, meta_tags(full, desc, slug + '/', 'og.jpg')))
        print('готово:', slug + '/index.html')

def write_service_files():
    """404.html, sitemap.xml, robots.txt. На странице 404 пути абсолютные: она открывается по любому адресу."""
    base = '/' + SITE.split('/', 3)[3]
    page = (f'<div class="page"><div class="lost">'
            f'<span class="code">404</span><h1>Такой страницы нет</h1>'
            f'<p>Адрес мог устареть или в нём опечатка. Отчёты по регионам собраны на главной.</p>'
            f'<p><a href="{base}">← Все регионы</a></p></div></div>')
    h = doc('Страница не найдена', page, 0, False, None, f'<link rel="icon" href="{base}favicon.png" type="image/png">\n<meta name="robots" content="noindex">')
    h = (h.replace('href="series.css', f'href="{base}series.css').replace('src="series.js', f'src="{base}series.js')
          .replace('href="fonts/', f'href="{base}fonts/'))
    open(os.path.join(ROOT, '404.html'), 'w', encoding='utf-8').write(h)
    urls = [SITE, SITE + 'trips/', SITE + 'about/'] + [SITE + pg['slug'] + '/' for pg in PAGES]
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    open(os.path.join(ROOT, 'robots.txt'), 'w', encoding='utf-8').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n')

def build(artifact=False):
    """Без аргументов собирает страницы на месте: index.html и <slug>/index.html рядом со скриптом.
    С ключом --artifact дополнительно кладёт в _artifact/ вариант со вшитыми стилями (для предпросмотра)."""
    local = VIDEO_BASE != VIDEO_SITE            # --local-video: пишем только index.local.html, страницы сайта не трогаем
    page_name = 'index.local.html' if local else 'index.html'
    ix = index_body()
    if artifact and not local:
        os.makedirs(os.path.join(ROOT, '_artifact'), exist_ok=True)
        open(os.path.join(ROOT, '_artifact', 'page.html'), 'w', encoding='utf-8').write(fragment(SERIES_TITLE, ix))
    if not local:
        open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(
            doc(SERIES_TITLE, ix, 0, False, None, meta_tags(SERIES_TITLE, INDEX_DESC, '', 'og.jpg')))
    for pg in PAGES:
        body = region_body(pg['slug'], pg['prev'], pg['next'])
        src = open(os.path.join(ROOT, 'src', pg['slug'] + '.html'), encoding='utf-8').read()
        m = re.search(r'<p class="hook">(.*?)</p>', src, re.S)
        desc = re.sub(r'<.*?>', '', m.group(1)).strip() if m else INDEX_DESC
        pg_meta = meta_tags(pg['title'] + ' · ' + SITE_NAME, desc, pg['slug'] + '/', pg['slug'] + '/og.jpg')
        os.makedirs(os.path.join(ROOT, pg['slug']), exist_ok=True)
        open(os.path.join(ROOT, pg['slug'], page_name), 'w', encoding='utf-8').write(
            doc(pg['title'], body, 1, False, region_style(pg['color'], pg['slug']), pg_meta))
        if artifact and not local:
            out = os.path.join(ROOT, '_artifact', pg['slug']); os.makedirs(out, exist_ok=True)
            open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(
                doc(pg['title'], body, 1, True, region_style(pg['color'], pg['slug'])))
        print('готово:', pg['slug'] + '/' + page_name)
    if not local:
        write_extra_pages()
        write_service_files()
        print('готово: index.html')
    return check_video()


def check_video():
    """Сверка: у каждого ролика, на который ссылается страница, есть файл в папке russia-video.
    Страница без ролика — это пустой чёрный прямоугольник на сайте, а старой копии в media/ больше нет.
    Если папки russia-video рядом нет (свежий клон, облачная сессия), проверить нечем — только предупреждение."""
    vdir = os.path.join(ROOT, 'russia-video')
    used = sorted(set(VIDEO_USED))
    if not os.path.isdir(vdir):
        print(f'внимание: папки russia-video рядом нет, {len(used)} роликов не проверены'); return True
    missing = [f'{s}/{n}' for s, n in used if not os.path.isfile(os.path.join(vdir, s, n)) or os.path.getsize(os.path.join(vdir, s, n)) == 0]
    stray = [p for p in (os.path.join(ROOT, s, 'media') for s in sorted({s for s, _ in used})) if os.path.isdir(p)
             and any(f.endswith('.mp4') for f in os.listdir(p))]
    if stray:
        print(f'внимание: в {len(stray)} папках media/ лежат ролики (например {os.path.relpath(stray[0], ROOT)}); их место — russia-video/, в основной репозиторий они не идут')
    if missing:
        print(f'ОШИБКА: {len(missing)} роликов нет в russia-video: ' + ', '.join(missing[:8]) + (' …' if len(missing) > 8 else ''))
        print('Выгрузите их (python tools/media.py export <регион> --video-only) или уберите со страницы.')
        return False
    print(f'ролики: {len(used)} ссылок, все файлы на месте в russia-video')
    return True


if __name__ == '__main__':
    import sys
    if '--local-video' in sys.argv:
        VIDEO_BASE = '../russia-video/'
    ok = build('--artifact' in sys.argv)
    if not ok and '--allow-missing-video' not in sys.argv:
        sys.exit(1)
