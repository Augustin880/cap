#!/usr/bin/env python3
"""CAP International School - static site generated from Pages CMS Markdown/JSON.
Run: python build.py. Output: HTML files at root for local preview and dist/ for hosting.
"""
from pathlib import Path
from html import escape as esc
import json,re,shutil,yaml
from urllib.parse import urlparse, unquote, quote
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
PAGE_DIR=ROOT/'content/pages'
ARTICLE_DIR=ROOT/'content/articles'
SITE=json.loads((ROOT/'content/site.json').read_text(encoding='utf-8'))
MD=MarkdownIt('commonmark', {'html':False,'linkify':True})
MD.enable('table')
HEADERS={
 'index':'index.html','ecole':'ecole.html','jurys':'jurys.html','transition':'transition.html',
 'deuxieme-degre':'deuxieme-degre.html','troisieme-degre':'troisieme-degre.html',
 'cap-en-plus':'cap-en-plus.html','examens':'examens.html','humaniste':'humaniste.html',
 'approche':'approche.html','equipe':'equipe.html','qui-sommes-nous':'qui-sommes-nous.html',
 'actualites':'actualites.html','dossiers':'dossiers.html','ecoute':'ecoute.html',
 'contact':'contact.html','radio':'radio.html','enseigner':'enseigner.html',
 'formations':'formations.html','archives':'archives.html'
}

# URLs made available as standalone navigable pages, not buried inside a parent page.
FORMATIONS=['jurys','transition','deuxieme-degre','troisieme-degre','cap-en-plus','examens','humaniste']
SCHOOL=['ecole','qui-sommes-nous','approche','equipe','ecoute','radio','enseigner']
ARCHIVE=['actualites','dossiers','archives']


def read_md(path):
 s=path.read_text(encoding='utf-8')
 if s.startswith('---\n'):
  _, fm, body=s.split('---\n',2)
  return yaml.safe_load(fm) or {},body.strip()
 return {},s.strip()
PAGES={p.stem:{'meta':read_md(p)[0],'body':read_md(p)[1]} for p in PAGE_DIR.glob('*.md')}
ARTICLES={p.stem:{'meta':read_md(p)[0],'body':read_md(p)[1]} for p in ARTICLE_DIR.glob('*.md')}


def t(v):return esc(str(v or ''), quote=True)
def public_path(src):
 src=str(src or '')
 return src[1:] if src.startswith('/media/') else src
def icon_arrow():
 return '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h16m-7-7 7 7-7 7"/></svg>'
def icon_out():
 return '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M5 19 19 5M8 5h11v11"/></svg>'
def btn(name,href,outline=False):
 return f'<a class="btn {"btn-outline" if outline else "btn-primary"}" href="{t(href)}"><span>{t(name)}</span><span class="btn-icon">{icon_arrow()}</span></a>'
def label(text):return f'<div class="section-kicker"><span class="kicker-dash"></span>{t(text)}</div>'
def pic(slug,alt='',priority=False):
 m=PAGES.get(slug,{}).get('meta',{})
 src=public_path(m.get('hero_image') or m.get('hero_photo_url') or SITE.get('home_photo_uploaded') or SITE.get('home_photo_url'))
 return f'<img src="{t(src)}" alt="{t(alt)}" loading="{ "eager" if priority else "lazy" }" decoding="async">' if src else ''

def localize_links(rendered):
 # Redirige les liens historiques internes vers les pages reconstruites.
 soup=BeautifulSoup(rendered, 'html.parser')
 routes={unquote(urlparse(item['meta'].get('source_url','')).path).rstrip('/').casefold(): HEADERS[key]
         for key,item in PAGES.items() if item['meta'].get('source_url') and key not in ('radio','enseigner')}
 for a in soup.select('a[href]'):
  href=a.get('href','')
  u=urlparse(href)
  if u.netloc and u.netloc.casefold() not in ('www.capinternationalschool.com','capinternationalschool.com'):continue
  path=unquote(u.path).rstrip('/').casefold()
  if path in routes and path!='':a['href']=routes[path]+(('#'+u.fragment) if u.fragment else '')
 return str(soup)

def get_title(slug):return PAGES.get(slug,{}).get('meta',{}).get('nav_label') or slug

def nav(active):
 menu=[('ecole','L’école'),('formations','Les formations'),('approche','Notre approche'),('actualites','Actualités')]
 top=''.join(f'<a class="nav-link {"active" if active==key or (key=="formations" and active in FORMATIONS) or (key=="ecole" and active in SCHOOL) else ""}" href="{HEADERS[key]}">{t(name)}</a>' for key,name in menu)
 mobile=''.join(f'<a class="mobile-link" href="{HEADERS[key]}">{t(name)}{icon_arrow()}</a>' for key,name in menu)
 # Distinct routes are listed as plain links; nav keeps only 5 main items.
 mobile_sub=''.join(f'<a class="mobile-sublink" href="{HEADERS[k]}">{t(get_title(k))}</a>' for k in FORMATIONS)
 logo=f'<img src="{t(public_path(SITE.get("logo", "media/logo-cap.png")))}" alt="Logo de CAP International School" width="62" height="62">'
 return f'''<div class="utility"><div class="container utility-inner"><span>{t(SITE['address_line_1'])} · {t(SITE['address_line_2'])}</span><a href="{t(SITE['phone_href'])}">{t(SITE['phone_label'])}</a></div></div>
<header class="site-header"><div class="container nav-shell"><a class="brand original-brand" href="index.html">{logo}<span class="brand-name">{t(SITE['site_name'])}</span></a><nav class="desktop-nav" aria-label="Navigation principale">{top}<a class="nav-contact {'active' if active=='contact' else ''}" href="contact.html">Contact <span>{icon_out()}</span></a></nav><button class="menu-toggle" id="menu-toggle" type="button" aria-label="Ouvrir le menu" aria-controls="mobile-nav" aria-expanded="false"><span></span><span></span></button></div>
<nav class="mobile-nav" id="mobile-nav" aria-label="Navigation mobile"><div class="mobile-inner">{mobile}<div class="mobile-menu-title">FORMATIONS</div>{mobile_sub}<a class="mobile-link mobile-contact" href="contact.html">Contact{icon_arrow()}</a></div></nav></header>'''


def footer():
 def col(title,slugs):
  return '<div class="footer-col"><h3>'+t(title)+'</h3>'+''.join(f'<a href="{HEADERS[k]}">{t(get_title(k))}</a>' for k in slugs)+'</div>'
 return f'''<footer class="site-footer"><div class="container footer-upper"><div class="footer-brand"><a href="index.html" class="footer-original-logo"><img src="{t(public_path(SITE.get("logo","media/logo-cap.png")))}" alt="CAP International School" width="88" height="88"><span>{t(SITE['site_name'])}</span></a><p>{t(SITE['motto'])}.</p></div>{col('L’école',SCHOOL[:4])}{col('Formations',FORMATIONS)}{col('Informations',['actualites','dossiers','radio','archives'])}<div class="footer-col footer-contact"><h3>Contact</h3><p>{t(SITE['address_line_1'])}<br>{t(SITE['address_line_2'])}</p><a href="{t(SITE['phone_href'])}">{t(SITE['phone_label'])}</a></div></div><div class="container footer-bottom"><span>© <span id="current-year"></span> {t(SITE['site_name'])}</span><a href="archives.html">Plan du site</a><a href="#top">Retour en haut ↑</a></div></footer>'''


def shell(slug,title,content,description=''):
 # All content is server-rendered static HTML, searchable without JavaScript.
 s=f'''<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#fffefa"><meta name="description" content="{t(description or title)}"><title>{t(title)} — {t(SITE['site_name'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet"><link rel="stylesheet" href="assets/style.css"><link rel="stylesheet" href="assets/v1-cms.css"><link rel="icon" type="image/png" href="{t(public_path(SITE.get("logo","media/logo-cap.png")))}"></head><body id="top">{nav(slug)}<main id="main">{content}</main>{footer()}<script src="assets/main.js" defer></script></body></html>'''
 return s


def home():
 # Hero copy is exclusively from the original site's home page, supplied as HTML.
 page=PAGES['index'];body=localize_links(MD.render(page['body']))
 h_title=SITE['home_hero_title']
 h_intro=SITE['home_hero_text']
 hero_pic=public_path(SITE.get('hero_photo_uploaded') or SITE.get('hero_photo_url'))
 img=f'<img src="{t(hero_pic)}" alt="Photographie illustrative d’étudiants" fetchpriority="high" decoding="async">' if hero_pic else ''
 hero=f'''<section class="home-hero"><div class="container hero-grid"><div class="hero-content"><div class="eyebrow"><span class="eyebrow-line"></span>{t(SITE['site_name'])}</div><h1 class="home-h1">{t(h_title)}</h1><p>{t(h_intro)}</p><div class="hero-actions">{btn('Nos écoles','formations.html')}{btn('Qui sommes-nous ?','qui-sommes-nous.html',True)}</div></div><div class="hero-visual"><div class="hero-arch"></div><div class="hero-photo">{img}</div><div class="hero-image-credit">PHOTOGRAPHIE D’ILLUSTRATION</div></div></div></section>'''
 intro=f'''<section class="section-pad home-intro" id="ecole"><div class="container intro-grid"><div class="intro-heading">{label('Une école ouverte sur le monde')}<h2>CAP, une formation <em>personnalisée.</em></h2></div><div class="intro-body"><p class="body-lead">{t(SITE['home_intro_1'])}</p><p>{t(SITE['home_intro_2'])}</p><a class="text-link" href="approche.html">Notre approche <span>{icon_arrow()}</span></a></div></div><div class="container"><div class="credo">{''.join('<div class="credo-item"><b>'+t(k)+'</b><p>'+t(v)+'</p></div>' for k,v in [(SITE['credo_1_title'],SITE['credo_1_text']),(SITE['credo_2_title'],SITE['credo_2_text']),(SITE['credo_3_title'],SITE['credo_3_text'])])}</div></div></section>'''
 cards=[('jurys','Préparation aux jurys'),('cap-en-plus','CAP EN PLUS'),('examens','Préparation aux examens')]
 card_html=''.join(f'''<article class="programme-card"><a class="programme-image" href="{HEADERS[k]}">{pic(k,'Photographie illustrative d’études')}<span class="programme-number">0{i+1}</span></a><div class="programme-body"><h3><a href="{HEADERS[k]}">{t(name)}</a></h3><a class="text-link" href="{HEADERS[k]}">En savoir plus <span>{icon_arrow()}</span></a></div></article>''' for i,(k,name) in enumerate(cards))
 programmes=f'''<section class="section-pad section-cream" id="parcours"><div class="container"><div class="section-head"><div>{label('Les écoles de CAP')}<h2>Nos <em>formations</em></h2></div><a class="text-link" href="formations.html">Toutes les formations <span>{icon_arrow()}</span></a></div><div class="programme-grid">{card_html}</div><a class="transition-banner" href="transition.html"><span class="transition-icon">2T</span><div><span>SEPTEMBRE 2026</span><h3>La deuxième transition ou 2T</h3></div><span class="transition-arrow">{icon_arrow()}</span></a></div></section>'''
 news=f'''<section class="section-pad"><div class="container"><div class="section-head"><div>{label('Actualités')}<h2>Actualités</h2></div><a class="text-link" href="actualites.html">Toutes les actualités <span>{icon_arrow()}</span></a></div><div class="news-grid home-news">{''.join(f'<a class="news-item" href="actualites.html"><span class="news-num">0{i+1}</span><h3>{t(title)}</h3><span class="news-card-arrow">{icon_arrow()}</span></a>' for i,title in enumerate([SITE['home_news_1'],SITE['home_news_2'],SITE['home_news_3']]))}</div></div></section>'''
 source=f'''<section class="section-pad section-cream archive-home"><div class="container"><details class="source-details"><summary><span>Contenu de l’accueil original</span><span class="expand-plus">+</span></summary><div class="rich-content">{body}</div></details></div></section>'''
 return hero+intro+programmes+news+source


def toc_for(html):
 soup=BeautifulSoup(html,'html.parser');heads=soup.find_all(['h2','h3'])
 if len(heads)<3:return html,''
 links=[]
 for idx,h in enumerate(heads):
  hid=f'section-{idx+1}';h['id']=hid
  label=h.get_text(' ',strip=True)
  links.append(f'<a href="#{hid}">{t(label)}</a>')
 return str(soup), '<aside class="section-index"><div class="section-index-title">Sur cette page</div>'+''.join(links)+'</aside>'


def page(slug):
 item=PAGES[slug];m=item['meta'];body=localize_links(MD.render(item['body']))
 body,contents=toc_for(body)
 desc=m.get('description','')
 intro=f'<p class="page-intro">{t(desc)}</p>' if desc and (desc.lower().strip(' .')!=m.get('title','').lower().strip(' .')) else ''
 if slug=='contact':
  # No introductory hero section; the contact card is the first content after the header.
  mail=SITE.get('contact_email','').strip()
  email=f'<a class="contact-value" href="mailto:{t(mail)}">{t(mail)}</a>' if mail else f'<a class="contact-value" href="{t(SITE["contact_original_url"])}" target="_blank" rel="noopener">E-mail {icon_out()}</a>'
  contact=f'''<section class="contact-clean section-pad"><div class="container contact-clean-grid"><div><div class="section-kicker"><span class="kicker-dash"></span>CONTACT</div><h1>{t(m['title'])}</h1><div class="contact-block"><small>CAP INTERNATIONAL SCHOOL</small><strong>{t(SITE['contact_person'])}</strong></div><div class="contact-block"><small>ADRESSE</small><strong>{t(SITE['address_line_1'])}<br>{t(SITE['address_line_2'])}</strong></div><div class="contact-block"><small>TÉLÉPHONE</small><a class="contact-value" href="{t(SITE['phone_href'])}">{t(SITE['phone_label'])}</a></div><div class="contact-block"><small>E-MAIL</small>{email}</div></div><div class="contact-map"><iframe loading="lazy" title="Carte de CAP International School à Wavre" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q={t(quote(SITE["address_line_1"]+", "+SITE["address_line_2"]+", Belgique"))}&amp;output=embed"></iframe></div></div>{('<div class="container"><div class="rich-content contact-extra">'+body+'</div></div>') if item['body'].strip() else ''}</section>'''
  return contact
 title=m.get('title') or get_title(slug)
 hero=f'''<section class="inner-hero slim-hero"><div class="container inner-hero-grid"><div class="inner-hero-content"><div class="breadcrumbs"><a href="index.html">Accueil</a><span>/</span>{t(m.get('nav_label',title))}</div>{label('CAP International School')}<h1>{t(title)}</h1>{intro}</div><div class="inner-hero-media">{pic(slug,'Photographie illustrative',True)}<span class="image-disclaimer">Photographie d’illustration</span></div></div></section>'''
 related=[]
 if slug in FORMATIONS:related=[x for x in FORMATIONS if x!=slug]
 elif slug in SCHOOL:related=[x for x in SCHOOL if x!=slug and x!='enseigner']
 elif slug in ARCHIVE:related=[x for x in ARCHIVE if x!=slug]
 related_html=''
 if related:
  related_html='<section class="section-pad related-section section-cream"><div class="container">'+label('À découvrir')+'<div class="related-links">'+''.join(f'<a href="{HEADERS[k]}">{t(get_title(k))}<span>{icon_arrow()}</span></a>' for k in related[:6])+'</div></div></section>'
 src=f'<a class="source-inline" href="{t(m.get("source_url"))}" rel="noopener" target="_blank">Page d’origine {icon_out()}</a>' if m.get('source_url') else ''
 return hero+f'<section class="section-pad reading-section"><div class="container reading-layout"><div class="rich-content">{body}</div><div class="reading-sidebar">{contents}{src}</div></div></section>'+related_html


def listing():
 def section(name,slugs):
  return f'<section class="directory-section"><h2>{t(name)}</h2><div class="directory-grid">'+''.join(f'''<a class="directory-card" href="{HEADERS[k]}"><span class="directory-photo">{pic(k,'Photographie illustrative')}</span><span class="directory-info"><b>{t(get_title(k))}</b><span>{icon_arrow()}</span></span></a>''' for k in slugs)+'</div></section>'
 return f'<section class="directory-head"><div class="container">{label("Nos écoles")}<h1>Les formations</h1></div></section><div class="container directory-body">'+section('Préparation et accompagnement', ['jurys','cap-en-plus','examens','transition'])+section('Les degrés', ['deuxieme-degre','troisieme-degre'])+section('Formation humaniste',['humaniste'])+'</div>'


def archives():
 # Site map also gives direct access to all secondary pages and the dated blog records.
 allpages=[('L’école',SCHOOL),('Les formations',FORMATIONS),('Actualités et dossiers',['actualites','dossiers','radio','enseigner'])]
 groups=''.join(f'<section class="archive-group"><h2>{t(title)}</h2><div class="archive-group-links">'+''.join(f'<a href="{HEADERS[k]}">{t(get_title(k))}{icon_arrow()}</a>' for k in keys)+'</div></section>' for title,keys in allpages)
 articles=''.join(f'<a href="article-{k}.html"><span>{t(v["meta"].get("date"))}</span><b>{t(v["meta"].get("title"))}</b>{icon_arrow()}</a>' for k,v in sorted(ARTICLES.items(),key=lambda item:item[1]['meta'].get('date',''),reverse=True))
 return '<section class="directory-head"><div class="container">'+label('CAP International School')+'<h1>Plan du site</h1></div></section><div class="container archive-layout">'+groups+'<section class="archive-group"><h2>Blog</h2><div class="archive-group-links">'+articles+'</div></section></div>'


def article(slug):
 obj=ARTICLES[slug];m=obj['meta'];body=MD.render(obj['body']);ref=m.get('source_url','')
 src=f'<a href="{t(ref)}" target="_blank" rel="noopener" class="source-inline">Article d’origine {icon_out()}</a>' if ref else ''
 return f'''<section class="directory-head"><div class="container"><div class="breadcrumbs"><a href="archives.html">Blog</a><span>/</span>{t(m.get('date'))}</div><h1 class="article-title">{t(m.get('title'))}</h1></div></section><section class="section-pad"><div class="container reading-layout"><div class="rich-content">{body}</div><div class="reading-sidebar">{src}</div></div></section>'''


def check_links(output):
 s=BeautifulSoup(output,'html.parser')
 return [a['href'] for a in s.select('a[href]') if a['href'].endswith('.html') and not (ROOT/a['href']).exists()]

def build():
 outputs={}
 for slug in PAGES:
  outputs[HEADERS[slug]]=shell(slug,PAGES[slug]['meta']['title'], home() if slug=='index' else page(slug))
 outputs['formations.html']=shell('formations','Les formations',listing())
 outputs['archives.html']=shell('archives','Plan du site',archives())
 for slug in ARTICLES:
  outputs['article-'+slug+'.html']=shell('archives',ARTICLES[slug]['meta']['title'],article(slug))
 for fn,html in outputs.items():
  (ROOT/fn).write_text(html,encoding='utf-8')
 dist=ROOT/'dist'
 if dist.exists():shutil.rmtree(dist)
 dist.mkdir()
 for p in ROOT.glob('*.html'):shutil.copy2(p,dist/p.name)
 shutil.copytree(ROOT/'assets',dist/'assets')
 shutil.copytree(ROOT/'media',dist/'media')
 print('Built',len(outputs),'HTML pages in root and dist')
 missing={f:check_links(html) for f,html in outputs.items() if check_links(html)}
 if missing:raise RuntimeError('Broken local links: '+str(missing))
 print('Link check OK')

if __name__=='__main__':build()
