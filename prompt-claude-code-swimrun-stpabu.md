# Prompt Claude Code — Swimrun de Saint-Pabu

> À coller tel quel au démarrage d'une session Claude Code, à la racine d'un dépôt vide.
> Les blocs `[À COMPLÉTER]` sont à remplir avant de lancer.

---

## 0. Ton rôle et ta méthode de travail

Tu es un développeur full-stack senior (Python / TypeScript / cartographie web). Tu vas construire deux outils pour l'organisation d'un Swimrun. Règles de travail :

1. **Avant d'écrire du code**, lis tout ce document, puis pose-moi uniquement les questions réellement bloquantes (maximum 5). Ensuite, propose un plan détaillé de la phase en cours et attends ma validation.
2. Tu travailles **phase par phase** (voir §10). À la fin de chaque phase : tu t'arrêtes, tu résumes ce qui a été fait, tu m'expliques comment le tester manuellement, et tu fais un commit Git clair (`feat(orga): import GPX par tronçon`).
3. Tu crées et tiens à jour un fichier **`CLAUDE.md`** à la racine : état d'avancement, décisions techniques et leur justification, pièges rencontrés, commandes utiles, prochaines étapes. Il doit permettre de reprendre le projet dans une nouvelle session sans perte de contexte.
4. Tu ne changes **pas la stack imposée** (§2) sans me demander. Si une contrainte te semble mauvaise, dis-le et argumente.
5. Pas de données en dur : tout ce qui est propre à l'événement (courses, horaires, allures, POI, marées, couleurs) est saisi ou importé.
6. Interface et messages utilisateur **en français**. Code, noms de variables et commentaires en anglais.

---

## 1. Contexte

- Événement : **Swimrun de Saint-Pabu** (Finistère, littoral de l'Aber Benoît). Formats XS et S, en solo ou en duo. Alternance de tronçons de course à pied et de natation en mer, sans zone de transition classique.
- Organisation bénévole, petite équipe, budget minimal.
- Deux outils **distincts** :
  - **Module 1 — Simulateur (privé)** : anticiper les flux de coureurs, la sécurité et la logistique.
  - **Module 2 — Site parcours (public)** : permettre aux participants de repérer le parcours, sur mobile et desktop.
- Le site public ne doit **jamais** exposer de données internes (allures, simulations, horaires de sécurité, comptes).

---

## 2. Contraintes techniques et stack imposée

### Hébergement : PythonAnywhere
- Une **seule web app WSGI** (le compte gratuit n'en autorise qu'une). Les deux modules cohabitent donc dans une même application Flask, mais dans des blueprints totalement séparés, de façon à pouvoir les scinder en deux web apps plus tard sans refonte.
- Pas de WebSocket, pas de tâche de fond persistante, pas de scheduler (APScheduler, Celery…) : tout le calcul de simulation se fait **côté navigateur**.
- Accès Internet sortant restreint depuis le serveur : **aucun appel à une API externe côté Python**. Les tuiles de carte sont chargées par le navigateur, ce qui est sans problème.
- Espace disque limité : dépendances Python légères (pas de GDAL, shapely, pyproj, pandas).
- CPU console limité : le **build front se fait en local** et les fichiers compilés sont versionnés et déployés tels quels.
- Base de données : **SQLite**.

### Backend
- Python (la version la plus récente proposée par PythonAnywhere, vérifie), **Flask 3**, Flask-Login, Flask-WTF (CSRF), Flask-SQLAlchemy (SQLAlchemy 2), **gpxpy**.
- Calculs géométriques en Python pur : distance haversine et projection locale équirectangulaire (suffisant à l'échelle de quelques km).
- Tests : **pytest**.

### Frontend
- **Vite + TypeScript + Vue 3** (Composition API, `<script setup>`), **Pinia** pour l'état partagé.
- Carte : **MapLibre GL JS** (rendu WebGL fluide, flèches le long des lignes, décalage de lignes natif).
- Géométrie : **Turf.js** en imports modulaires (`@turf/along`, `@turf/line-slice-along`, `@turf/length`…).
- Graphique de marée : **Chart.js** + `chartjs-plugin-annotation` (curseur vertical).
- Styles : CSS natif avec **variables CSS (design tokens)** dans un fichier de thème unique. Pas de framework CSS lourd.
- Tests : **Vitest** pour la logique pure (simulation, formatage).
- Vite en **build multi-pages** : deux points d'entrée indépendants (`orga` et `public`) produisant deux bundles séparés dans `backend/app/static/dist/`, avec `manifest.json` lu par un helper Jinja. Le bundle public ne doit contenir aucun code du simulateur.
- En développement : serveur Vite avec proxy `/api` vers Flask.

### Fonds de carte
- Satellite par défaut : **orthophotos IGN via la Géoplateforme** (`data.geopf.fr`, WMTS, couche `ORTHOIMAGERY.ORTHOPHOTOS`, sans clé). Vérifie l'URL exacte et les conditions dans la documentation IGN.
- Fallback satellite : Esri World Imagery (attribution obligatoire).
- Couche « plan » secondaire commutable (OSM ou Plan IGN).
- Attributions affichées correctement sur toutes les cartes.

---

## 3. Architecture cible

```
swimrun-stpabu/
├── CLAUDE.md
├── README.md                 # installation locale + déploiement PythonAnywhere
├── backend/
│   ├── wsgi.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py       # create_app()
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── core/             # Python pur, sans Flask, testable isolément
│   │   │   ├── filenames.py  # parsing des noms de fichiers GPX
│   │   │   ├── gpx_import.py # lecture, nettoyage, assemblage des tronçons
│   │   │   ├── geometry.py   # haversine, projection locale, rééchantillonnage
│   │   │   ├── overlaps.py   # détection des tronçons empruntés plusieurs fois
│   │   │   ├── tides.py      # interpolation de la hauteur d'eau
│   │   │   └── publish.py    # génération des JSON statiques du site public
│   │   ├── orga/             # blueprint privé, préfixe /orga, login requis
│   │   ├── public/           # blueprint public, préfixe /
│   │   ├── templates/
│   │   └── static/dist/      # build Vite (versionné)
│   ├── data/
│   │   ├── uploads/          # GPX bruts
│   │   └── published/        # JSON consommés par le site public
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── shared/           # init carte, fonds de carte, thème, utils Turf
│       ├── orga/             # app Vue du simulateur
│       └── public/           # app Vue du site parcours
└── docs/
    └── brand/                # logo et captures de l'identité visuelle
```

**Principe de découplage** : le site public ne lit **que** des fichiers JSON statiques générés par une action « Publier » dans l'espace orga (`data/published/`, avec un hash de version pour le cache). Le site public fonctionne donc même si le module orga est en cours de modification, et il reste très léger à servir.

---

## 4. Données : import des GPX par tronçon

### Convention de nommage
`Course{N}_Tronçon{M}_{Run|Swim}.gpx` — exemples : `Course1_Tronçon1_Run.gpx`, `Course1_Tronçon2_Swim.gpx`.

- Parsing insensible à la casse, accepte `Tronçon` et `Troncon`.
- **Normaliser l'Unicode (NFC) avant le parsing** : les noms de fichiers venant de macOS encodent souvent `ç` en NFD, ce qui casse une regex naïve.
- `Run` → allure course à pied ; `Swim` → allure natation. Aucune gestion du dénivelé ni des courants.
- Un fichier au nom non conforme est rejeté avec un message explicite (pas d'échec silencieux).

### Lecture et assemblage
- Lire tous les `trkpt` de tous les `trkseg` dans l'ordre ; à défaut, les `rtept`. Ignorer altitude et horodatage.
- Supprimer les points consécutifs dupliqués.
- Trier les tronçons par numéro, calculer la longueur de chacun et les distances cumulées.
- Assembler un tracé continu par course, en conservant pour chaque point l'index du tronçon et son type.

### Contrôles à l'import (écran de prévisualisation avant validation)
- Tableau : course, n° de tronçon, type, longueur, nombre de points, statut.
- **Erreur** : numéro de tronçon en double, type inconnu, fichier illisible, tronçon vide.
- **Avertissement** : numéro manquant dans la séquence, écart > 30 m entre la fin d'un tronçon et le début du suivant (seuil configurable), tronçon de natation anormalement long.
- Réimporter une course remplace proprement ses tronçons.

### Détection des passages multiples (calculée à l'import, côté Python)
- Rééchantillonner le tracé tous les ~5 m.
- Un point est en « passage multiple » s'il existe un autre point du même tracé à moins de **12 m** (configurable) mais séparé de plus de **200 m** en distance cumulée.
- Fusionner les points contigus en segments (longueur minimale ~30 m), puis grouper les segments qui se superposent physiquement.
- Sortie par course : liste de groupes, chacun contenant ses passages ordonnés (`passage 1`, `passage 2`…) avec distance de début et de fin sur le tracé.
- Tests pytest sur un tracé synthétique aller-retour et sur une boucle en « 8 ».

---

## 5. Module 1 — Simulateur (privé)

### Accès
- Blueprint `/orga`, authentification Flask-Login, protection CSRF.
- Comptes créés via une commande CLI (`flask create-user`), pas d'inscription en ligne.

### Paramétrage
- **Événement** : date, nom, fuseau `Europe/Paris`.
- **Courses** (jusqu'à 3 simultanées) : nom, couleur, **heure de départ indépendante**, tronçons importés.
- **Allures par course**, saisies manuellement, fixes :
  - Premier coureur : course à pied en `mm:ss /km`, natation en `mm:ss /100 m`.
  - Dernier coureur : idem.
  - Validation : le premier doit être plus rapide que le dernier sur chaque discipline.

### Modèle de calcul (TypeScript, fonctions pures, testées avec Vitest)
- `timeline(course, profil)` : pour chaque tronçon, heure d'entrée et de sortie = cumul de `longueur × allure du type`.
- `distanceAt(course, profil, t)` : distance parcourue sur le tracé à l'instant `t`.
  - Avant le départ : pas de position.
  - Après l'arrivée : bloqué à la distance totale.
- **La « plage »** d'une course à l'instant `t` = portion du tracé comprise entre `distanceAt(dernier)` et `distanceAt(premier)`.
- Cas de test de référence : tronçon 1 Run de 1000 m à 5:00/km, tronçon 2 Swim de 200 m à 2:00/100 m. À `t = départ + 6 min`, la position doit être **1050 m** (1000 m de course en 5 min, puis 50 m de nage en 1 min).

### Affichage cartographique
- Les 3 courses sur la même carte satellite, chacune dans sa couleur, avec visibilité activable par course et légende.
- Plage rendue comme une **bande épaisse semi-transparente** le long du tracé (épaisseur interpolée selon le zoom), extraite avec `lineSliceAlong`. Si plusieurs courses partagent une portion, léger décalage latéral (`line-offset`) pour que chaque bande reste visible.
- Marqueurs « tête » et « queue » de peloton ; au survol ou au clic : heure, km, tronçon en cours, type.
- Tronçons de natation visuellement distincts des tronçons de course (trait pointillé par exemple).
- Panneau latéral par course : état (pas parti / en course / terminé), km de la tête et de la queue, tronçon et type en cours pour chacun, étalement du peloton en mètres et en minutes.

### Contrôle temporel
- Barre de défilement couvrant automatiquement `[premier départ − 15 min ; dernière arrivée du dernier coureur + 15 min]`, pas de 10 s.
- Bouton **Lecture / Pause**, vitesses ×1, ×10, ×30, ×60, ×120.
- Horloge `HH:MM:SS` bien visible, champ pour sauter directement à une heure précise.
- Raccourci clavier : espace = lecture/pause.
- Animation via `requestAnimationFrame`, mise à jour des sources GeoJSON sans aucun appel serveur pendant la lecture.
- Horloge unique partagée dans un store Pinia, source de vérité pour la carte et le graphique de marée.

### Module Marée
- **Saisie des données** (aucune API externe) :
  - Option A : tableau des pleines et basses mers (date-heure, hauteur en m, PM/BM) recopié depuis les tables SHOM du port choisi, idéalement avec les extrêmes de la veille et du lendemain pour interpoler les bords.
  - Option B : import CSV `datetime;hauteur_m`.
  - **Sélecteur du fuseau de la source** à la saisie (UTC, UTC+1 ou heure légale selon la table utilisée). Stockage en UTC, affichage en `Europe/Paris`.
- **Interpolation** (Option A) entre deux extrêmes successifs, en cosinus :
  `h(t) = h1 + (h2 − h1) × (1 − cos(π × (t − t1) / (t2 − t1))) / 2`
  Implémentée dans `core/tides.py` (tests pytest) ; le backend fournit une série échantillonnée toutes les 5 min au front.
- **Graphique 2D** : hauteur d'eau sur la plage horaire de la simulation, marqueurs PM/BM, **curseur vertical synchronisé** avec l'horloge de simulation.
- Affichage de la valeur courante : `Hauteur d'eau : 4,32 m — marée montante`.
- Cliquer sur le graphique déplace l'horloge de simulation à l'heure correspondante.

### Gestion des POI (alimente le site public)
- CRUD simple : type (ravitaillement, entrée dans l'eau, sortie de l'eau, bouée directionnelle), nom, course(s) concernée(s), coordonnées, description courte.
- Pour les bouées : côté de passage (`à laisser à gauche` / `à droite`).
- Placement par **clic sur la carte** pour remplir les coordonnées.
- Le km de chaque POI est calculé automatiquement par projection sur le tracé de la course.

### Publication
- Bouton « Publier le parcours » : génère dans `data/published/` les fichiers `meta.json`, `course-{id}.geojson` (tracé, tronçons, types, passages multiples) et `pois-{id}.json`, **sans aucune donnée d'allure ou de simulation**.
- Affiche la date de dernière publication et un aperçu du site public.

---

## 6. Module 2 — Site parcours (public)

### Généralités
- Blueprint `/`, aucune authentification, **mobile-first**, responsive desktop.
- Consomme uniquement les JSON publiés.
- Sélecteur de course (onglets) si plusieurs courses sont publiées.
- Métadonnées de partage (Open Graph), favicon issu du logo.
- Accessibilité : contrastes suffisants, slider manipulable au clavier, libellés ARIA.

### Carte
- Fond **satellite par défaut** (orthophotos IGN), commutateur vers une couche plan.
- Tracé avec un **liseré clair** sous la ligne colorée pour rester lisible sur l'imagerie sombre (rochers, mer).
- Tronçons de natation et de course visuellement distincts, avec légende.
- **Flèches directionnelles** régulièrement espacées le long du tracé (couche `symbol` MapLibre avec `symbol-placement: line`), orientées dans le sens de course.

### Tronçons empruntés plusieurs fois
- Chaque passage est **décalé latéralement** (`line-offset`) avec une teinte ou un motif propre et ses propres flèches, pour que les deux sens restent lisibles côte à côte.
- Pastilles numérotées « 1 » / « 2 » à l'entrée de chaque passage, et mention dans la légende (« Portion empruntée 2 fois »).
- Quand le curseur du slider se trouve dans une portion multiple, **mettre en avant le passage actif** et atténuer l'autre, avec un message du type : « 2ᵉ passage — vous revenez vers la plage ».

### Slider kilométrique
- Barre de 0 à X km (pas de 10 m), gros curseur tactile.
- Sous la barre : **bande colorée par type de tronçon** (course / natation) et repères des POI, pour lire le parcours d'un coup d'œil.
- En manipulant le slider, un marqueur se déplace d'avant en arrière sur le tracé (`turf.along`).
- Encart d'information : km courant, tronçon `N / total` et son type, distance restante sur le tronçon, prochain POI et sa distance.
- Option « Suivre le curseur » (la carte se recentre) et bouton lecture pour un défilement automatique.

### Points d'intérêt
- Icônes cliquables distinctes : ravitaillement, entrée dans l'eau, sortie de l'eau, bouée directionnelle.
- Au clic : popup sur desktop, **bottom sheet** sur mobile, avec nom, km, description et, pour les bouées, le côté de passage.
- Un clic sur un POI peut positionner le slider à son kilométrage.

### Performance
- Chargement initial rapide sur réseau mobile faible : bundle public minimal, JSON compacts, cache HTTP avec hash de version.

---

## 7. Identité visuelle

Référence : compte Instagram de l'événement (`@swimrunstpabu`). Tu n'y as pas accès : je dépose dans `docs/brand/` le logo et quelques captures de publications.

- Extrais une palette à partir de ces fichiers (script Python avec Pillow) et **propose-moi 2 variantes de thème** avant de les appliquer.
- Toutes les couleurs, typographies, rayons et ombres passent par des variables CSS dans un fichier de thème unique partagé par les deux modules.
- Polices auto-hébergées (pas de CDN Google Fonts).
- Ton visuel : convivial, littoral breton, lisible avant tout sur la carte satellite.

`[À COMPLÉTER si déjà connus]`
- Couleur principale : `#______`
- Couleur secondaire : `#______`
- Police titres / texte : `______`

---

## 8. Qualité

- `core/` Python et la logique de simulation TypeScript couverts par des tests unitaires (pytest, Vitest).
- Jeu de données de démonstration : si mes vrais GPX ne sont pas encore dans le dépôt, génère des GPX synthétiques réalistes autour de Saint-Pabu (≈ 48.565 N, 4.596 W) avec 3 courses, alternance Run/Swim et au moins une portion aller-retour.
- Lint et formatage : ruff (Python), ESLint + Prettier (front).
- Gestion d'erreurs visible pour l'utilisateur (import, publication, saisie des marées).
- Secrets (`SECRET_KEY`) via variables d'environnement, jamais versionnés.

---

## 9. Déploiement PythonAnywhere

Le `README.md` doit documenter pas à pas :
1. Build front en local (`npm run build`) et commit du dossier `static/dist/`.
2. Récupération du code sur PythonAnywhere (`git pull`) et création du virtualenv.
3. Configuration du fichier WSGI.
4. **Mapping des fichiers statiques** dans l'onglet Web (`/static/` → dossier `static/`) pour qu'ils soient servis sans passer par Flask.
5. Variables d'environnement, création de la base et du premier compte orga.
6. Rechargement de la web app et check-list de vérification.

---

## 10. Plan de développement par phases

Arrête-toi et attends ma validation à la fin de chaque phase.

| Phase | Contenu | Critère d'acceptation |
|---|---|---|
| **P0** | Questions bloquantes, `CLAUDE.md`, squelette Flask + Vite multi-pages, une carte satellite affichée sur `/` et `/orga`, **premier déploiement test sur PythonAnywhere** | Les deux pages s'affichent en ligne avec le fond satellite |
| **P1** | `core/` : parsing des noms, import GPX, assemblage, contrôles, détection des passages multiples + tests | `pytest` vert, y compris noms NFD et tracé aller-retour |
| **P2** | Orga : login, événement, courses, écran d'import avec prévisualisation, affichage des tracés | Import de 3 courses et affichage correct |
| **P3** | Simulation : allures, horloge, plage, lecture/pause, panneau d'état + tests Vitest | Cas de référence à 1050 m validé, animation fluide |
| **P4** | Module marée : saisie, interpolation, graphique synchronisé | Curseur de marée synchrone, clic = saut dans le temps |
| **P5** | POI (CRUD, clic carte, km auto) et publication des JSON | JSON publiés sans aucune donnée privée |
| **P6** | Site public : carte, flèches, passages multiples, slider km, POI, mobile | Parcours lisible et navigable sur smartphone |
| **P7** | Thème, finitions responsive, performance, README de déploiement | Déploiement reproductible depuis le README |

---

## 11. Hors périmètre V1 (ne pas développer, mais ne pas bloquer l'architecture)

- Suivi GPS en direct des participants.
- Dénivelé, courants marins, variation d'allure au fil de la course.
- Mode hors-ligne / PWA avec tuiles en cache.
- Comptes participants, inscriptions.
- Tableau des horaires de passage par point (ouverture/fermeture des ravitaillements, présence des kayaks de sécurité) : à envisager en V2, le modèle `timeline()` doit le permettre.
- Gestion de plusieurs éditions ou événements.
