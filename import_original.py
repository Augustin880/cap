#!/usr/bin/env python3
"""Importe (sur la machine de l'utilisateur) les contenus HTML du site Jimdo.

But : obtenir une copie fidèle, modifiable par Pages CMS, sans fabriquer de textes.
IMPORTANT : ce script n'est pas déclenché automatiquement pendant un build : il ne
peut donc pas écraser silencieusement les modifications faites dans Pages CMS.

Utilisation :
  pip install -r requirements.txt
  python import_original.py --all --force
  python build.py

Pour une page bloquée, placez le HTML sauvegardé dans source/<slug>.html puis :
  python import_original.py --all --local-first --force
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote
import argparse,re,sys,yaml,requests
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as to_md

ROOT=Path(__file__).resolve().parent
PAGES=ROOT/'content/pages'
LOCAL=ROOT/'source'
LOCAL.mkdir(exist_ok=True)

# La correspondance source -> slug est explicite, pour ne pas créer de contenu inventé.
def read(path):
 s=path.read_text(encoding='utf-8')
 if not s.startswith('---\n'):
  raise ValueError(f'Pas de frontmatter YAML dans {path}')
 _,front,body=s.split('---\n',2)
 return yaml.safe_load(front) or {},body

def write(path,meta,body):
 path.write_text('---\n'+yaml.safe_dump(meta,sort_keys=False,allow_unicode=True,width=130)+'---\n'+body.strip()+'\n',encoding='utf-8')

def make_soup(html):
 soup=BeautifulSoup(html,'html.parser')
 for node in soup(['script','style','noscript']): node.decompose()
 return soup

# Si le HTML est une copie Jimdo, le contenu original se trouve dans #content_area.
def content_from_jimdo(html,base_url):
 soup=make_soup(html)
 container=soup.select_one('#content_area')
 if container is None:
  container=soup.select_one('#content_start') or soup.select_one('main')
 if container is None:
  raise RuntimeError('Structure HTML introuvable (ni #content_area ni <main>).')
 # Modules finaux seulement. Ne jamais convertir le conteneur j-hgrid lui-même,
 # car ses sous-modules seraient alors reproduits plusieurs fois.
 kinds=('j-header','j-text','j-textWithImage','j-imageSubtitle','j-fileDownload','j-download','j-video','j-htmlCode')
 fragments=[]
 for module in container.select('.j-module'):
  cl=set(module.get('class') or [])
  if not cl.intersection(kinds):continue
  if 'j-htmlCode' in cl: continue # code tiers / iframe, non éditable comme texte
  item=BeautifulSoup(str(module),'html.parser')
  for bad in item.select('[data-display="cms-only"], .cc-clear'): bad.decompose()
  for img in item.select('img'):
   src=img.get('data-src') or img.get('src') or ''
   img['src']=urljoin(base_url,src)
   img.attrs.pop('srcset',None);img.attrs.pop('sizes',None)
  for link in item.select('a[href]'):
   target=link.get('href') or ''
   if target.startswith('javascript:') or target=='#':link.unwrap();continue
   link['href']=urljoin(base_url,target)
  if 'j-header' in cl:
   first=item.find(re.compile(r'^h[1-6]$'))
   if first:
    level=2 if first.name in ('h1','h2') else 3
    fragments.append('#'*level+' '+first.get_text(' ',strip=True))
    continue
  if 'j-textWithImage' in cl:
   node=item.select_one('.cc-m-textwithimage-inline-rte')
   # Intègre le texte sans les scripts et conserve le lien de l'image du module.
   im=item.find('img')
   if im and im.get('src'):
    alt=im.get('alt') or ''
    fragments.append('!['+alt+']('+im['src']+')')
   if node:item=node
  raw=to_md(str(item),heading_style='ATX').strip()
  raw=re.sub(r'\n{3,}','\n\n',raw)
  raw=re.sub(r'\n\s+\n','\n\n',raw)
  if raw and raw not in {'.','\\.','—'}:fragments.append(raw)
 if not fragments:
  # fallback text only, used if Jimdo's layout changes.
  article=container
  content=to_md(str(article),heading_style='ATX').strip()
  if not content:raise RuntimeError('Contenu vide : la page a peut-être été bloquée.')
  return content
 result='\n\n'.join(fragments)
 return re.sub(r'\n{3,}','\n\n',result).strip()

def retrieve(session,url):
 errors=[]
 for target in [url+'?mobile=1' if '?' not in url else url+'&mobile=1',url]:
  try:
   res=session.get(target,timeout=24)
   res.raise_for_status()
   if '<html' not in res.text[:3000].lower():
    raise RuntimeError('Réponse non HTML')
   return res.text
  except Exception as e:errors.append(str(e))
 raise RuntimeError('; '.join(errors))

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--all',action='store_true',help='Importer les pages publiques et articles')
 parser.add_argument('--force',action='store_true',help='Autoriser le remplacement du texte existant')
 parser.add_argument('--local-first',action='store_true',help='Utiliser source/<slug>.html si présent')
 parser.add_argument('--slug',help='Importer uniquement une page identifiée par son nom de fichier sans .md')
 args=parser.parse_args()
 if not (args.all or args.slug):parser.error('Utilisez --all ou --slug=...')
 if not args.force:parser.error('Ajoutez --force pour confirmer le remplacement des contenus CMS existants')
 files=list(PAGES.glob('*.md'))
 if args.slug:files=[p for p in files if p.stem==args.slug]
 if not files:parser.error('Aucune page correspondante')
 session=requests.Session()
 session.headers.update({'User-Agent':'Mozilla/5.0 (compatible; CAPContentMigration/1.0; educational website migration)','Accept-Language':'fr-BE,fr;q=0.9'})
 done=[];fail=[]
 for path in sorted(files):
  meta,old=read(path)
  slug=path.stem
  source_url=meta.get('source_url','')
  local_path=LOCAL/(slug+'.html')
  try:
   if slug in ('radio','enseigner') and not local_path.exists():
    # Rubriques partagées, mieux migrer leur HTML sauvegardé explicitement.
    print('SKIP',slug,'(ajouter source/'+slug+'.html)')
    continue
   if args.local_first and local_path.exists():
    html=local_path.read_text(encoding='utf-8')
   else:
    if not source_url:raise RuntimeError('source_url manquant')
    if slug=='index' and local_path.exists():
     html=local_path.read_text(encoding='utf-8')
    else:html=retrieve(session,source_url)
   body=content_from_jimdo(html,source_url)
   if len(body.strip())<20:raise RuntimeError('Contenu récupéré trop court')
   write(path,meta,body)
   done.append((slug,len(body)))
   print('OK',slug,len(body),'caractères')
  except Exception as e:
   fail.append((slug,str(e)))
   print('ERREUR',slug,str(e)[:180],file=sys.stderr)
 print('\nImportées:',len(done),'Ignorées / en échec:',len(fail))
 for slug,reason in fail:print(' -',slug,reason[:180])
 print('Le contenu d’une page bloquée reste inchangé : aucun texte de remplacement n’est inventé.')
 print('Ensuite: python build.py')
 return 0 if not fail else 1

if __name__=='__main__':sys.exit(main())
