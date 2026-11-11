#!/usr/bin/env python3
"""Generate the public site from the documents edited in Pages CMS."""
from pathlib import Path
from html import escape as esc
from urllib.parse import urlparse, unquote, quote
import json
import re
import shutil
import yaml
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SITE = json.loads((ROOT / 'content/site.json').read_text(encoding='utf-8'))
UI = json.loads((ROOT / 'content/ui.json').read_text(encoding='utf-8'))
MD = MarkdownIt('commonmark', {'html': False, 'linkify': True})
MD.enable('table')

ROUTES = {
    'index': 'index.html', 'ecole': 'ecole.html', 'jurys': 'jurys.html',
    'transition': 'transition.html', 'deuxieme-degre': 'deuxieme-degre.html',
    'troisieme-degre': 'troisieme-degre.html', 'cap-en-plus': 'cap-en-plus.html',
    'examens': 'examens.html', 'humaniste': 'humaniste.html',
    'approche': 'approche.html', 'equipe': 'equipe.html',
    'qui-sommes-nous': 'qui-sommes-nous.html', 'actualites': 'actualites.html',
    'dossiers': 'dossiers.html', 'ecoute': 'ecoute.html',
    'contact': 'contact.html', 'radio': 'radio.html', 'enseigner': 'enseigner.html',
    'formations': 'formations.html', 'archives': 'archives.html',
}
FORMATIONS = ['jurys', 'transition', 'deuxieme-degre', 'troisieme-degre',
              'cap-en-plus', 'examens', 'humaniste']
SCHOOL = ['ecole', 'qui-sommes-nous', 'approche', 'equipe', 'ecoute', 'radio', 'enseigner']
RESOURCES = ['actualites', 'dossiers', 'archives']


def read_md(path):
    source = path.read_text(encoding='utf-8')
    if source.startswith('---\n'):
        _, front, body = source.split('---\n', 2)
        return {'meta': yaml.safe_load(front) or {}, 'body': body.strip()}
    return {'meta': {}, 'body': source.strip()}


PAGES = {file.stem: read_md(file) for file in (ROOT / 'content/pages').glob('*.md')}
ARTICLES = {file.stem: read_md(file) for file in (ROOT / 'content/articles').glob('*.md')}


def t(value):
    return esc(str(value if value is not None else ''), quote=True)


def shared(key, override=None):
    """Defaults are shared, but individual page fields can diverge independently."""
    if override and str(override.get(key, '') or '').strip():
        return str(override[key]).strip()
    return str(SITE.get(key, '') or '').strip()


def phone_link(label):
    """Make the clickable link from the displayed phone, so editors enter it once."""
    number = re.sub(r'[^0-9+]', '', label or '')
    if number.startswith('00'):
        number = '+' + number[2:]
    elif number.startswith('0') and not number.startswith('00'):
        number = '+32' + number[1:]
    elif number and not number.startswith('+'):
        number = '+' + number
    return 'tel:' + number if number else ''


def public_path(value):
    value = str(value or '').strip()
    if value.startswith('/media/') or value.startswith('/assets/'):
        return value[1:]
    return value


def photo(primary, fallback=''):
    return public_path(primary or fallback)


def page_image(slug):
    meta = PAGES.get(slug, {}).get('meta', {})
    return photo(meta.get('hero_image'), meta.get('hero_photo_url'))


def img(src, alt='', priority=False):
    if not src:
        return ''
    return (f'<img src="{t(public_path(src))}" alt="{t(alt)}" '
            f'loading="{"eager" if priority else "lazy"}" decoding="async">')


def pic(slug, priority=False):
    meta = PAGES.get(slug, {}).get('meta', {})
    return img(page_image(slug), meta.get('hero_image_alt') or UI['page_image_note'], priority)


def arrow():
    return '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16m-7-7 7 7-7 7"/></svg>'


def out_icon():
    return '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M5 19 19 5M8 5h11v11"/></svg>'


def btn(text, href, outline=False):
    return f'<a class="btn {"btn-outline" if outline else "btn-primary"}" href="{t(href)}"><span>{t(text)}</span><span class="btn-icon">{arrow()}</span></a>'


def label(text):
    return f'<div class="section-kicker"><span class="kicker-dash"></span>{t(text)}</div>'


def get_title(slug):
    return PAGES.get(slug, {}).get('meta', {}).get('nav_label') or slug


def decode_protected_email(fragment):
    try:
        data = bytes.fromhex(fragment)
        return ''.join(chr(byte ^ data[0]) for byte in data[1:]) if len(data) > 1 else ''
    except (ValueError, IndexError):
        return ''


def localize_links(markup):
    soup = BeautifulSoup(markup, 'html.parser')
    old_urls = {}
    for slug, entry in PAGES.items():
        original = entry['meta'].get('source_url', '')
        if original and slug not in ('radio', 'enseigner'):
            old_urls[unquote(urlparse(original).path).rstrip('/').casefold()] = ROUTES[slug]
    for slug, entry in ARTICLES.items():
        original = entry['meta'].get('source_url', '')
        if original:
            old_urls[unquote(urlparse(original).path).rstrip('/').casefold()] = f'article-{slug}.html'
    old_urls[''] = 'index.html'
    for link in list(soup.select('a[href]')):
        text = link.get_text(' ', strip=True).casefold()
        if any(x in text for x in ('page d’origine', "page d'origine", 'article d’origine',
                                    "article d'origine", 'site d’origine', "site d'origine")):
            link.decompose()
    for element in soup.select('[href], [src]'):
        for attr in ('href', 'src'):
            url = element.get(attr, '')
            if not url:
                continue
            parsed = urlparse(url)
            if attr == 'href' and '/cdn-cgi/l/email-protection' in parsed.path and parsed.fragment:
                address = decode_protected_email(parsed.fragment)
                if '@' in address:
                    element[attr] = 'mailto:' + address
                continue
            if url.startswith('/media/'):
                element[attr] = url[1:]
                continue
            if attr != 'href' or parsed.scheme not in ('', 'http', 'https'):
                continue
            if parsed.netloc and parsed.netloc.casefold() not in ('www.capinternationalschool.com',
                                                                    'capinternationalschool.com'):
                continue
            if not parsed.path and not parsed.netloc:
                continue
            path = unquote(parsed.path).rstrip('/').casefold()
            if path in old_urls:
                suffix = ('?' + parsed.query if parsed.query else '') + ('#' + parsed.fragment if parsed.fragment else '')
                element[attr] = old_urls[path] + suffix
    return str(soup)


def navigation(active):
    menu = [
        ('ecole', UI['nav_school']), ('formations', UI['nav_courses']),
        ('approche', UI['nav_approach']), ('actualites', UI['nav_news']),
    ]
    def is_active(slug):
        return active == slug or (slug == 'formations' and active in FORMATIONS) or (slug == 'ecole' and active in SCHOOL)
    top = ''.join(f'<a class="nav-link {"active" if is_active(slug) else ""}" href="{ROUTES[slug]}">{t(name)}</a>' for slug, name in menu)
    mobile = ''.join(f'<a class="mobile-link" href="{ROUTES[slug]}">{t(name)}{arrow()}</a>' for slug, name in menu)
    sub = ''.join(f'<a class="mobile-sublink" href="{ROUTES[slug]}">{t(get_title(slug))}</a>' for slug in FORMATIONS)
    logo = img(SITE.get('logo'), SITE['site_name'], priority=True)
    top_phone = shared('phone_label', {'phone_label': SITE.get('header_phone_label', '')})
    tel_html = f'<a href="{t(phone_link(top_phone))}">{t(top_phone)}</a>' if top_phone else ''
    address = ' · '.join(filter(None, (SITE.get('header_address_line_1') or SITE.get('address_line_1', ''), SITE.get('header_address_line_2') or SITE.get('address_line_2', ''))))
    utility = f'<div class="utility"><div class="container utility-inner"><span>{t(address)}</span>{tel_html}</div></div>'
    return f'''{utility}<header class="site-header"><div class="container nav-shell"><a class="brand original-brand" href="index.html">{logo}<span class="brand-name">{t(SITE['site_name'])}</span></a><nav class="desktop-nav" aria-label="{t(UI['navigation_aria_label'])}">{top}<a class="nav-contact {'active' if active=='contact' else ''}" href="contact.html">{t(UI['nav_contact'])} <span>{out_icon()}</span></a></nav><button class="menu-toggle" id="menu-toggle" type="button" aria-label="{t(UI['menu_open'])}" data-menu-open="{t(UI['menu_open'])}" data-menu-close="{t(UI['menu_close'])}" aria-controls="mobile-nav" aria-expanded="false"><span></span><span></span></button></div><nav class="mobile-nav" id="mobile-nav" aria-label="{t(UI['navigation_mobile_aria_label'])}"><div class="mobile-inner">{mobile}<div class="mobile-menu-title">{t(UI['mobile_courses_heading'])}</div>{sub}<a class="mobile-link mobile-contact" href="contact.html">{t(UI['nav_contact'])}{arrow()}</a></div></nav></header>'''


def footer():
    def col(title, pages):
        return '<div class="footer-col"><h3>' + t(title) + '</h3>' + ''.join(f'<a href="{ROUTES[slug]}">{t(get_title(slug))}</a>' for slug in pages) + '</div>'
    footer_phone = SITE.get('footer_phone_label') or SITE.get('phone_label', '')
    addr1 = SITE.get('footer_address_line_1') or SITE.get('address_line_1', '')
    addr2 = SITE.get('footer_address_line_2') or SITE.get('address_line_2', '')
    tel = f'<a href="{t(phone_link(footer_phone))}">{t(footer_phone)}</a>' if footer_phone else ''
    return f'''<footer class="site-footer"><div class="container footer-upper"><div class="footer-brand"><a href="index.html" class="footer-original-logo">{img(SITE.get('logo'), SITE['site_name'])}<span>{t(SITE['site_name'])}</span></a><p>{t(SITE.get('motto', ''))}</p></div>{col(UI['footer_school'], SCHOOL[:4])}{col(UI['footer_courses'], FORMATIONS)}{col(UI['footer_information'], ['actualites', 'dossiers', 'radio', 'archives'])}<div class="footer-col footer-contact"><h3>{t(UI['footer_contact'])}</h3><p>{t(addr1)}<br>{t(addr2)}</p>{tel}</div></div><div class="container footer-bottom"><span>© <span id="current-year"></span> {t(SITE['site_name'])}</span><a href="archives.html">{t(UI['footer_sitemap'])}</a><a href="#top">{t(UI['footer_back_top'])}</a></div></footer>'''


def shell(slug, title, markup, description=''):
    logo = public_path(SITE.get('logo', ''))
    return f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#fffefa"><meta name="description" content="{t(description or title)}"><title>{t(title)} — {t(SITE['site_name'])}</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet"><link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/v1-cms.css"><link rel="icon" type="image/png" href="{t(logo)}"></head><body id="top" class="page-{t(slug)}">{navigation(slug)}<main id="main">{markup}</main>{footer()}<script src="assets/main.js" defer></script></body></html>'''


def home():
    item = PAGES['index']
    m = item['meta']
    body = localize_links(MD.render(item['body']))
    src = page_image('index')
    hero = f'''<section class="home-hero"><div class="container hero-grid"><div class="hero-content"><div class="eyebrow"><span class="eyebrow-line"></span>{t(SITE['site_name'])}</div><h1 class="home-h1">{t(m.get('home_hero_title'))}</h1><p>{t(m.get('home_hero_text'))}</p><div class="hero-actions">{btn(m.get('primary_button'), 'formations.html')}{btn(m.get('secondary_button'), 'qui-sommes-nous.html', True)}</div></div><div class="hero-visual"><div class="hero-arch"></div><div class="hero-photo">{img(src, m.get('hero_image_alt') or UI['page_image_note'], True)}</div><div class="hero-image-credit">{t(UI['page_image_note'])}</div></div></div></section>'''
    values = [(m.get(f'credo_{i}_title', ''), m.get(f'credo_{i}_text', '')) for i in (1, 2, 3)]
    motto_html = ''.join('<div class="credo-item"><b>' + t(key) + '</b><p>' + t(val) + '</p></div>' for key,val in values if key or val)
    intro = f'''<section class="section-pad home-intro" id="ecole"><div class="container intro-grid"><div class="intro-heading">{label(m.get('intro_kicker'))}<h2>{t(m.get('intro_title'))} <em>{t(m.get('intro_title_emphasis'))}</em></h2></div><div class="intro-body"><p class="body-lead">{t(m.get('home_intro_1'))}</p><p>{t(m.get('home_intro_2'))}</p><a class="text-link" href="approche.html">{t(m.get('approach_link'))}<span>{arrow()}</span></a></div></div><div class="container"><div class="credo">{motto_html}</div></div></section>'''
    cards = m.get('program_cards') or []
    card_markup = ''
    for idx, card in enumerate(cards):
        slug = str(card.get('page') or '')
        if slug not in ROUTES:
            continue
        card_markup += f'''<article class="programme-card"><a class="programme-image" href="{ROUTES[slug]}">{pic(slug)}<span class="programme-number">{idx+1:02}</span></a><div class="programme-body"><h3><a href="{ROUTES[slug]}">{t(card.get('title') or get_title(slug))}</a></h3><a class="text-link" href="{ROUTES[slug]}">{t(m.get('program_card_link'))}<span>{arrow()}</span></a></div></article>'''
    programmes = f'''<section class="section-pad section-cream" id="parcours"><div class="container"><div class="section-head"><div>{label(m.get('program_kicker'))}<h2>{t(m.get('program_heading'))} <em>{t(m.get('program_heading_emphasis'))}</em></h2></div><a class="text-link" href="formations.html">{t(m.get('program_link'))}<span>{arrow()}</span></a></div><div class="programme-grid">{card_markup}</div><a class="transition-banner" href="transition.html"><span class="transition-icon">{t(m.get("transition_badge"))}</span><div><span>{t(m.get('transition_date'))}</span><h3>{t(m.get('transition_title'))}</h3></div><span class="transition-arrow">{arrow()}</span></a></div></section>'''
    featured = ''
    for idx, entry in enumerate(m.get('news') or []):
        href = entry.get('link') or 'actualites.html'
        featured += f'''<a class="news-item" href="{t(href)}"><span class="news-num">{idx+1:02}</span><h3>{t(entry.get('title'))}</h3><span class="news-card-arrow">{arrow()}</span></a>'''
    news = f'''<section class="section-pad"><div class="container"><div class="section-head"><div>{label(m.get('news_heading'))}<h2>{t(m.get('news_heading'))}</h2></div><a class="text-link" href="actualites.html">{t(m.get('news_link'))}<span>{arrow()}</span></a></div><div class="news-grid home-news">{featured}</div></div></section>'''
    extra = f'''<section class="section-pad section-cream archive-home"><div class="container"><details class="source-details"><summary><span>{t(m.get('additional_info_heading'))}</span><span class="expand-plus">+</span></summary><div class="rich-content">{body}</div></details></div></section>''' if body else ''
    return hero + intro + programmes + news + extra


def toc_for(markup):
    soup = BeautifulSoup(markup, 'html.parser')
    headings = soup.find_all(['h2', 'h3'])
    if len(headings) < 3:
        return markup, ''
    links = []
    for idx, heading in enumerate(headings):
        identifier = f'section-{idx+1}'
        heading['id'] = identifier
        links.append(f'<a href="#{identifier}">{t(heading.get_text(" ", strip=True))}</a>')
    return str(soup), '<aside class="section-index"><div class="section-index-title">' + t(UI['toc_heading']) + '</div>' + ''.join(links) + '</aside>'


def contact_page(m, body):
    """Independent optional page values, otherwise use shared school details."""
    person = shared('contact_person', m)
    addr1 = shared('address_line_1', m)
    addr2 = shared('address_line_2', m)
    phone = shared('phone_label', m)
    email = shared('contact_email', m)
    title = m.get('title', '')
    blocks = ''
    if person:
        blocks += f'<div class="contact-block"><small>{t(UI["contact_person_label"])}</small><strong>{t(person)}</strong></div>'
    if addr1 or addr2:
        blocks += f'<div class="contact-block"><small>{t(UI["contact_address_label"])}</small><strong>{t(addr1)}<br>{t(addr2)}</strong></div>'
    if phone:
        blocks += f'<div class="contact-block"><small>{t(UI["contact_phone_label"])}</small><a class="contact-value" href="{t(phone_link(phone))}">{t(phone)}</a></div>'
    if email:
        blocks += f'<div class="contact-block"><small>{t(UI["contact_email_label"])}</small><a class="contact-value" href="mailto:{t(email)}">{t(email)}</a></div>'
    # Explicit map query can differ from the postal address; otherwise keep them synchronized.
    query = m.get('map_query') or ', '.join(part for part in (addr1, addr2, SITE.get('country', '')) if part)
    show = m.get('show_map', True) is not False and bool(query)
    map_title = m.get('map_title') or SITE['site_name']
    map_html = f'''<div class="contact-map"><iframe loading="lazy" title="{t(map_title)}" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q={t(quote(query))}&amp;output=embed"></iframe></div>''' if show else ''
    extra = f'<div class="container"><div class="rich-content contact-extra">{body}</div></div>' if body.strip() else ''
    return f'''<section class="contact-clean section-pad"><div class="container contact-clean-grid"><div>{label(UI['contact_kicker'])}<h1>{t(title)}</h1>{blocks}</div>{map_html}</div>{extra}</section>'''


def page(slug):
    item = PAGES[slug]
    m = item['meta']
    body = localize_links(MD.render(item['body']))
    body, index = toc_for(body)
    if slug == 'contact':
        return contact_page(m, body)
    title = m.get('title') or get_title(slug)
    desc = m.get('description', '')
    intro = f'<p class="page-intro">{t(desc)}</p>' if desc and desc.lower().strip(' .') != str(title).lower().strip(' .') else ''
    hero = f'''<section class="inner-hero slim-hero"><div class="container inner-hero-grid"><div class="inner-hero-content"><div class="breadcrumbs"><a href="index.html">{t(UI['page_home'])}</a><span>/</span>{t(get_title(slug))}</div>{label(SITE['site_name'])}<h1>{t(title)}</h1>{intro}</div><div class="inner-hero-media">{pic(slug, True)}<span class="image-disclaimer">{t(UI['page_image_note'])}</span></div></div></section>'''
    if slug in FORMATIONS:
        related = [x for x in FORMATIONS if x != slug]
    elif slug in SCHOOL:
        related = [x for x in SCHOOL if x != slug and x != 'enseigner']
    elif slug in RESOURCES:
        related = [x for x in RESOURCES if x != slug]
    else:
        related = []
    related_markup = ''
    if related:
        cards = ''.join(f'<a href="{ROUTES[x]}">{t(get_title(x))}<span>{arrow()}</span></a>' for x in related[:6])
        related_markup = f'<section class="section-pad related-section section-cream"><div class="container">{label(UI["related_heading"])}<div class="related-links">{cards}</div></div></section>'
    sidebar = f'<div class="reading-sidebar">{index}</div>' if index else ''
    cls = 'reading-layout' if index else 'reading-layout reading-layout--single'
    return hero + f'<section class="section-pad reading-section"><div class="container {cls}"><div class="rich-content">{body}</div>{sidebar}</div></section>' + related_markup


def listing():
    meta = PAGES['formations']['meta']
    def section(title, slugs):
        cards = ''.join(f'''<a class="directory-card" href="{ROUTES[x]}"><span class="directory-photo">{pic(x)}</span><span class="directory-info"><b>{t(get_title(x))}</b><span>{arrow()}</span></span></a>''' for x in slugs)
        return f'<section class="directory-section"><h2>{t(title)}</h2><div class="directory-grid">{cards}</div></section>'
    head = f'<section class="directory-head"><div class="container">{label(UI["courses_kicker"])}<h1>{t(meta.get("title"))}</h1></div></section>'
    intro = localize_links(MD.render(PAGES['formations']['body']))
    intro_html = f'<div class="rich-content">{intro}</div>' if intro else ''
    return head + '<div class="container directory-body">' + intro_html + section(meta.get('section_preparation'), ['jurys', 'cap-en-plus', 'examens', 'transition']) + section(meta.get('section_degrees'), ['deuxieme-degre', 'troisieme-degre']) + section(meta.get('section_humanist'), ['humaniste']) + '</div>'


def archive_listing():
    meta = PAGES['archives']['meta']
    groups = [(meta.get('group_school'), SCHOOL), (meta.get('group_courses'), FORMATIONS),
              (meta.get('group_resources'), ['actualites', 'dossiers', 'radio', 'enseigner'])]
    markup = ''
    for title, slugs in groups:
        links = ''.join(f'<a href="{ROUTES[x]}">{t(get_title(x))}{arrow()}</a>' for x in slugs)
        markup += f'<section class="archive-group"><h2>{t(title)}</h2><div class="archive-group-links">{links}</div></section>'
    all_articles = sorted(ARTICLES.items(), key=lambda entry: entry[1]['meta'].get('date', ''), reverse=True)
    articles = ''.join(f'''<a href="article-{slug}.html"><span>{t(entry["meta"].get("date"))}</span><b>{t(entry["meta"].get("title"))}</b>{arrow()}</a>''' for slug, entry in all_articles)
    markup += f'<section class="archive-group"><h2>{t(meta.get("group_blog"))}</h2><div class="archive-group-links">{articles}</div></section>'
    intro = localize_links(MD.render(PAGES['archives']['body']))
    intro_html = f'<div class="rich-content">{intro}</div>' if intro else ''
    return f'<section class="directory-head"><div class="container">{label(SITE["site_name"])}<h1>{t(meta.get("title"))}</h1></div></section><div class="container archive-layout">{intro_html}{markup}</div>'


def article(slug):
    entry = ARTICLES[slug]
    m = entry['meta']
    body = localize_links(MD.render(entry['body']))
    image = photo(m.get('image'), m.get('image_url'))
    picture = f'<div class="article-main-image">{img(image, m.get("image_alt") or UI["page_image_note"])}</div>' if image else ''
    content = f'<section class="section-pad"><div class="container reading-layout reading-layout--single"><div class="rich-content">{picture}{body}</div></div></section>' if picture or body else ''
    return f'''<section class="directory-head"><div class="container"><div class="breadcrumbs"><a href="archives.html">{t(UI['blog_heading'])}</a><span>/</span>{t(m.get('date'))}</div><h1 class="article-title">{t(m.get('title'))}</h1></div></section>{content}'''


def validate_local_links(outputs):
    filenames = set(outputs) | {'assets/style.css', 'assets/v1-cms.css', 'assets/main.js'}
    errors = []
    for name, markup in outputs.items():
        soup = BeautifulSoup(markup, 'html.parser')
        anchors = {x.get('id') for x in soup.select('[id]')}
        for node in soup.select('[href], [src]'):
            for attr in ('href', 'src'):
                raw = node.get(attr, '')
                parsed = urlparse(raw)
                if not raw or parsed.scheme or parsed.netloc:
                    continue
                path = unquote(parsed.path).lstrip('/')
                if path and path not in filenames and not (ROOT / path).is_file():
                    errors.append(f'{name}: missing {raw}')
                elif parsed.fragment and not path and unquote(parsed.fragment) not in anchors:
                    errors.append(f'{name}: missing anchor {raw}')
    return errors


def build():
    outputs = {}
    for slug, entry in PAGES.items():
        if slug in ('formations', 'archives'):
            continue
        contents = home() if slug == 'index' else page(slug)
        outputs[ROUTES[slug]] = shell(slug, entry['meta'].get('title', ''), contents, entry['meta'].get('description', ''))
    for slug, builder in (('formations', listing), ('archives', archive_listing)):
        entry = PAGES[slug]
        outputs[ROUTES[slug]] = shell(slug, entry['meta']['title'], builder(), entry['meta'].get('description', ''))
    for slug, entry in ARTICLES.items():
        outputs[f'article-{slug}.html'] = shell('archives', entry['meta'].get('title', ''), article(slug))
    missing = validate_local_links(outputs)
    if missing:
        raise RuntimeError('Broken internal links:\n' + '\n'.join(missing))
    dist = ROOT / 'dist'
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir()
    for name, markup in outputs.items():
        (ROOT / name).write_text(markup, encoding='utf-8')
        (dist / name).write_text(markup, encoding='utf-8')
    shutil.copytree(ROOT / 'assets', dist / 'assets')
    shutil.copytree(ROOT / 'media', dist / 'media')
    print(f'Built {len(outputs)} pages. Local links OK.')


if __name__ == '__main__':
    build()
