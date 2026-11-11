# CAP International School — Refonte sur base de V1, avec Pages CMS

Version statique HTML, JavaScript, CSS. Palette et composants visuels dérivés de la **V1** (bleu profond, ivoire, cuivre ; grand hero photographique). Le logo CAP fourni remplace le logo inventé en V1.

## Ouvrir le site

Le site est **déjà généré** à la racine : ouvrir `index.html` ou servir le dossier avec :

```sh
python -m http.server 8000
```

Puis : `http://localhost:8000/`.

## Pages et navigation

- Menu principal volontairement limité à **L'école / Les formations / Notre approche / Actualités / Contact**.
- Toutes les pages de formation sont des pages HTML autonomes ; l'index complet se trouve dans `formations.html`.
- Les pages secondaires, dossiers, ressources audio et articles du blog figurent dans `archives.html` et dans le pied de page.
- La première section/hero de **Contact est supprimée**. Le contenu commence immédiatement par les coordonnées, puis la carte.
- Logo CAP original dans `media/logo-cap.png`.
- Photos d'illustration **non IA**, URL Unsplash conservées de la V1. Remplacer par des photos autorisées de l'établissement si possible.

## Éditer avec Pages CMS

1. Créer un dépôt GitHub et placer **tous les fichiers** de ce projet à sa racine, notamment `.pages.yml` (fichier caché).
2. Se connecter sur https://app.pagescms.org/ avec GitHub et autoriser l'application Pages CMS à accéder au dépôt.
3. Ouvrir le dépôt dans Pages CMS :
   - **Identité, accueil et coordonnées** : nom de l'école, logo, téléphone, adresse, e-mail, hero et photos.
   - **Pages et contenus** : titre, description, photo et **texte intégral** de chacune des pages HTML.
   - **Articles du blog** : ajout et modification des billets.
4. Enregistrer les modifications dans Pages CMS. Elles sont ajoutées dans le dépôt GitHub.
5. Configurer le déploiement afin que le site soit regénéré après chaque changement (voir ci-dessous).

## Déployer sur Cloudflare Pages

Connecter le dépôt GitHub à Cloudflare Pages.

- **Build command** : `pip install -r requirements.txt && python build.py`
- **Build output directory** : `dist`
- **Root directory** : laisser vide, racine du dépôt.

Tout changement enregistré via Pages CMS déclenche un nouveau déploiement si la branche GitHub est connectée à Cloudflare Pages.

## Importer le contenu original de Jimdo (important)

Les textes visibles **déjà présents** dans cette livraison comprennent le texte intégral de l'accueil fourni en HTML, des informations tirées du site source, ainsi que les noms, liens et catégories de toutes les rubriques. Les détails des autres pages sont provisoirement des **relevés factuels**, pas une copie intégrale de chaque texte. Le script ci-dessous permet d'importer les contenus du site original **sans réécriture**, dans des champs éditables du CMS.

Exécuter **une seule fois, avant les premières modifications dans Pages CMS** :

```sh
pip install -r requirements.txt
python import_original.py --all --local-first --force
python build.py
```

Le script récupère le HTML public de chaque page Jimdo ; les paragraphes, listes, titres, liens et images sont transformés en Markdown. Il remplace le champ `body` des fichiers `content/pages/*.md`, qui deviennent éditables dans Pages CMS. **Il n'est pas exécuté pendant les builds normaux** pour ne jamais écraser les modifications éditoriales.

### Pages de l'ancien site refusant l'accès automatique

Certaines URL secondaires renvoient **403 Forbidden**. Le script ne prétend pas avoir importé ce qui n'a pas pu être lu : il affiche une erreur et laisse le texte existant intact. Pour ces pages, enregistrer le HTML d'origine dans `source/<slug>.html`, par exemple `source/equipe.html`, puis relancer :

```sh
python import_original.py --slug=equipe --local-first --force
python build.py
```

Attention : la commande `--force` remplace le texte actuel de la page concernée. Faire une sauvegarde/commit avant de la lancer.

L'accueil fourni a été enregistré dans `source/index.html` et importé une première fois. Le contenu intégral des **cinq interviews Radio Antipode** et les documents PDF sont des fichiers externes **liés** vers les originaux, non dupliqués dans le dépôt ; leurs liens restent éditables dans `radio.md` et `dossiers.md`. Il faut vérifier que les fichiers d'origine sont encore disponibles ; certains téléchargements passent par des redirections Jimdo.

**E-mail :** l'adresse est protégée/masquée sur la page source accessible automatiquement. Le champ `contact_email` est laissé vide plutôt que d'inventer une adresse. Renseigner l'adresse officielle dans Pages CMS : elle s'affichera alors comme lien `mailto:`.

**Textes historiques :** les annonces datées (2012 à 2026) ont été conservées comme telles. C'est à l'équipe de l'école de décider quelles informations sont toujours valables avant mise en ligne.

## Structure

| Emplacement | Fonction |
|---|---|
| `.pages.yml` | Configuration Pages CMS |
| `content/site.json` | Données globales modifiables |
| `content/pages/*.md` | Pages principales et secondaires, titres et contenu |
| `content/articles/*.md` | Billets de blog |
| `source/index.html` | Source HTML de l'accueil fournie |
| `import_original.py` | Import Jimdo vers Markdown éditable |
| `build.py` | Générateur HTML statique |
| `assets/style.css` | Feuille de style V1 originale |
| `assets/v1-cms.css` | Mise en page V1 ajustée |
| `media/` | Logo et photos à téléverser |
| `dist/` | Site final construit pour Cloudflare Pages |

## Limites

- Cette version est une **maquette de refonte** non officielle.
- Les textes qui n'ont pas été fournis en HTML ou récupérés automatiquement ne sont **pas présentés comme une transcription intégrale**. Les liens vers les pages d'origine restent disponibles, ainsi que l'importeur permettant de les intégrer.
- Le contact n'inclut pas de formulaire d'envoi : aucune boîte de réception ou traitement de données n'a été configuré. Téléphone et accès à l'e-mail d'origine sont présents.
- Vérifier les droits d'exploitation des textes, photos, documents et fichiers audio avant publication.
