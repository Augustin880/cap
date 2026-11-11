# CAP International School — Site et Pages CMS

Le site conserve le design de la V1. Les textes et images visibles proviennent des fichiers dans `content/`. Les fichiers HTML sont **générés** : il ne faut pas les modifier pour changer un texte.

## Modifier le site (sans toucher au code)

Ouvrir [Pages CMS](https://app.pagescms.org/), puis le dépôt `Augustin880/cap`.

Les rubriques apparaissent dans cet ordre :

1. **Pages principales** — l'accueil et la page Contact.
2. **Formations** — le sommaire, les jurys, CAP EN PLUS, les degrés et les autres parcours.
3. **École et équipe** — les pages de présentation et les photographies.
4. **Actualités et ressources** — les articles, dossiers et le plan du site.
5. **Identité et navigation** — le logo, les coordonnées générales, les menus et les textes communs.

Un titre, une image ou un paragraphe d'une page se change dans **la page concernée**. Les photographies peuvent être remplacées par l'outil d'import d'images. Les textes longs s'éditent dans le champ « Contenu de la page ».

### Coordonnées : une saisie commune, des différences possibles

Dans **Identité et navigation → Coordonnées générales et identité**, saisir l'adresse, le téléphone et l'e-mail généraux. Le site les reprend là où aucune valeur plus spécifique n'a été renseignée.

Dans **Pages principales → Contact**, les champs téléphone, e-mail, adresse et nom sont facultatifs :

- Laisser le champ **vide** pour afficher la valeur générale.
- Renseigner une **valeur spécifique** seulement si la page Contact doit afficher une information différente.

Dans les coordonnées générales, les éventuelles valeurs spécifiques pour le haut de page et le pied de page (adresses et téléphones) fonctionnent de la même façon.

Le numéro de téléphone se saisit sous une seule forme lisible (`0471 31 32 63`) : le lien d'appel est automatiquement généré. Il n'y a **pas de second champ** `tel:` à maintenir.

La carte Contact utilise par défaut l'adresse affichée sur Contact. Son champ « Adresse de la carte » ne doit être rempli que si le point sur la carte est différent.

### Les images

Pour chaque page, utiliser le champ **Image de la page**. Quand aucune image n'a encore été importée, l'illustration externe existante reste affichée. Il n'est pas nécessaire de renseigner deux fois un lien et une image.

Le logo se modifie uniquement dans **Identité et navigation → Coordonnées générales et identité**. Il est réutilisé dans l'en-tête, le pied de page et l'icône du site.

Les images insérées au milieu du texte d'une page se modifient dans l'éditeur de texte de cette page. Pour les articles, il y a un champ « Image de l'article » indépendant.

### La page d'accueil

Les textes d'introduction, les trois valeurs pédagogiques, les cartes de formation, la mise en avant de la 2T et les actualités mises en avant se modifient **tous dans Accueil**.

Les éléments des actualités en vedette ont chacun leur titre et leur lien : ils peuvent différer de la page vers laquelle ils renvoient. Les pages de formation conservent elles aussi leurs titres propres ; changer un titre de carte sur l'accueil n'impose pas de modifier celui de la page de formation.

### Ajouter ou modifier un article

Ouvrir **Actualités et ressources → Articles du blog**. Choisir un article existant ou en créer un nouveau. Saisir le titre, la date, le contenu et éventuellement une image.

## Publier sur GitHub Pages

Les modifications enregistrées dans Pages CMS créent un commit dans GitHub. Le workflow `.github/workflows/pages.yml` exécute `python build.py` et publie le dossier `dist`.

Dans **GitHub → Settings → Pages → Build and deployment**, sélectionner **Source : GitHub Actions**. Ne pas choisir « Deploy from a branch » avec des fichiers source non reconstruits.

Le script peut également être lancé localement :

```bash
pip install -r requirements.txt
python build.py
```

Le contenu du site est dans `content/pages/`, `content/articles/`, `content/site.json` et `content/ui.json`. Le dossier `dist/` est généré et ne doit pas être édité à la main.

## Mise en place du correctif

Copier uniquement les fichiers du ZIP au même emplacement, en conservant les dossiers. **Ne pas supprimer** `content/pages/` ni `content/articles/` : les textes importés déjà présents sont préservés. Les deux nouvelles pages de configuration `content/pages/formations.md` et `content/pages/archives.md` sont nécessaires pour que leurs textes de sommaire soient modifiables.
