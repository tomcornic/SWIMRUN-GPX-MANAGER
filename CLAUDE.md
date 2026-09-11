# CLAUDE.md — Swimrun de Saint-Pabu

Contexte complet du projet : voir `prompt-claude-code-swimrun-stpabu.md` à la racine (cahier des charges, stack imposée, plan de phases).

## État d'avancement

- **P0 terminé** : squelette Flask + Vite multi-pages, carte satellite IGN affichée sur `/` et `/orga`.
  - ✅ Dépôt Git initialisé (local uniquement, pas de remote).
  - ✅ Backend Flask : `create_app()`, blueprints `orga` (`/orga`) et `public` (`/`), helper `vite_asset()` pour lire le manifest Vite.
  - ✅ Frontend Vite multi-pages (`orga` + `public`), MapLibre GL JS avec fond IGN orthophotos (WMTS, sans clé), Pinia initialisé (pas encore de store).
  - ✅ Build front testé, deux pages testées en local (`curl` + vérification directe de la tuile WMTS).
  - ⏳ Déploiement PythonAnywhere réel : **reporté** à la demande de l'utilisateur. Code et README prêts, mais pas encore déployé.
- **P1 terminé** : `core/` (parsing, import GPX, assemblage, détection des passages multiples), jeu de données de démo.
  - ✅ `core/filenames.py` : parsing `Course{N}_Tronçon{M}_{Run|Swim}.gpx`, NFC avant regex, erreurs explicites (nom invalide / type inconnu).
  - ✅ `core/geometry.py` : haversine, projection équirectangulaire locale, rééchantillonnage par distance.
  - ✅ `core/gpx_import.py` : lecture GPX (trkpt, fallback rtept), dédoublonnage des points consécutifs, contrôles (tronçon vide, fichier illisible, natation anormalement longue) et assemblage d'une course (numéro en double, numéro manquant, écart > 30 m entre tronçons).
  - ✅ `core/overlaps.py` : détection des passages multiples (voir décision ci-dessous pour le détail de l'algorithme).
  - ✅ 28 tests pytest verts (`filenames`, `geometry`, `gpx_import`, `overlaps` — y compris nom NFD et un tracé aller-retour + un tracé en « 8 » simplifié), `ruff check` propre.
  - ✅ `backend/scripts/generate_demo_gpx.py` : génère 3 courses synthétiques autour de Saint-Pabu (`backend/data/demo/`, versionné), avec un aller-retour sur Course 2 / tronçon 3. Pipeline entier revalidé sur ce jeu de données (import + assemblage + détection).
  - ⏳ Pas encore d'écran d'import ni de persistance (DB, réimport qui remplace les tronçons) — c'est le rôle de P2, `core/` reste volontairement pur Python sans Flask ni DB.
- **P2 terminé** : auth, base de données, CRUD événement/courses, écran d'import avec prévisualisation, affichage des tracés.
  - ✅ Modèles SQLAlchemy 2.0 (`User`, `Event`, `Course`, `Troncon` avec points stockés en JSON), SQLite dans `backend/data/app.db` (gitignored).
  - ✅ Auth Flask-Login + CSRF (Flask-WTF) : `/orga/login`, `/orga/logout`, toutes les routes `/orga/*` protégées par `@login_required`. Comptes créés via `flask create-user` (pas d'inscription en ligne, conforme §5).
  - ✅ Paramétrage : événement (nom, date — fuseau Europe/Paris fixe, non éditable), courses (nom, couleur, heure de départ), max 3 courses simultanées imposé côté route.
  - ✅ Écran d'import : upload multi-fichiers → aperçu (tableau statut/erreurs/avertissements, réutilise `core/gpx_import`) → validation séparée qui persiste (remplace proprement les tronçons existants de la course, voir décision ci-dessous pour le bug rencontré sur le filtrage par numéro de course).
  - ✅ Affichage des tracés : endpoint `/orga/courses/<id>/trace.geojson`, rendu sur la carte MapLibre du dashboard (`frontend/src/orga/App.vue` + `shared/map.ts::addCourseTrack`).
  - ✅ 45 tests pytest verts (auth, CRUD événement/courses, flux d'import complet avec les GPX de démo de P1, y compris réimport et rejet sur erreur), `ruff check` propre.
  - ✅ Parcours complet revalidé sur un vrai serveur `flask run` (pas seulement le client de test) : login → événement → course → upload → aperçu → validation → `trace.geojson` → carte, plus vérification que les routes protégées redirigent bien sans session.

## Décisions techniques et justification

- **Cible Python locale = 3.11-compatible**, même si la machine de dev a Python 3.14 installé. Raison : PythonAnywhere gratuit propose 3.11/3.12/3.13 selon la date de création du compte — éviter toute syntaxe post-3.11 pour ne pas se faire piéger au déploiement.
- **Versions des dépendances front figées à jour au 2026-09-11** (vue 3.5.42, maplibre-gl 6.9.0, vite 8.3.0, vue-tsc 3.3.11, typescript 5.9.3) plutôt qu'aux versions initialement supposées — un premier `npm install` a révélé un décalage important avec les versions attendues. **`vitest` est volontairement figé en `^4.1.11`** (pas la 5.x) : la 5.x fait planter `npm@10.8.2` (bug arborist connu, `Cannot read properties of null (reading 'edgesOut')`) et on ne peut pas monter npm 12 sans Node ≥22 (on a Node 20.20.2 en local). À réévaluer si l'environnement Node change.
- **Manifest Vite** : avec Vite 8, `manifest.json` est généré dans `dist/.vite/manifest.json` (pas à la racine de `dist/`). Le helper `backend/app/vite.py` lit ce chemin.
- **CSS des chunks partagés** : `orga` et `public` importent tous les deux `shared/map.ts`, donc Rollup les fusionne dans un chunk commun (`map-*.js` / `map-*.css`) au lieu de dupliquer le CSS dans chaque entrée. Le helper `vite_asset()` doit donc parcourir récursivement les `imports` du manifest pour retrouver tout le CSS associé — un premier essai qui ne lisait que `chunk.css` de l'entrée oubliait le CSS de MapLibre (la carte s'affichait sans son CSS). Corrigé.
- **WMTS IGN orthophotos** : URL KVP validée en conditions réelles (tuile récupérée et affichée pour Saint-Pabu, voir ci-dessous) :
  `https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&TILEMATRIXSET=PM_0_19&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}`
  Pas de clé requise. Fallback Esri (§2 du cahier des charges) pas encore implémenté — prévu quand le sélecteur de fond de carte sera construit (P6/P7).
- **`node --check`** est autorisé sans confirmation dans `.claude/settings.json` (vérif de syntaxe seule, sans exécution).
- **Algorithme de détection des passages multiples** (`core/overlaps.py`) : le cahier des charges (§4) décrit le principe à haut niveau (rééchantillonnage 5 m, points proches < 12 m mais éloignés > 200 m sur le tracé, fusion en segments ≥ 30 m, puis regroupement des segments qui se superposent). L'implémentation resserre ce principe :
  - Pour chaque point rééchantillonné, on ne garde que sa **meilleure correspondance spatiale** (plus proche voisin respectant `min_gap_m`), pas toutes les correspondances possibles — sinon une ligne droite aller-retour produit un faisceau de correspondances voisines qui fragmente un seul couloir en plusieurs (bogue rencontré et corrigé, voir tests).
  - Les correspondances (i, j) forment une diagonale dans la grille des indices ; on les regroupe en « couloirs » par continuité d'indices, chaque couloir donnant deux passages (un par extrémité de la correspondance).
  - Près d'un demi-tour (aller-retour), la zone `min_gap_m` autour du point de rebroussement exclut la vraie symétrique de quelques points, ce qui peut scinder un même couloir en deux groupes quasi identiques à quelques mètres près. Une passe de fusion post-traitement (`_merge_overlapping_groups`) recolle ces groupes quasi-doublons — c'est aussi une lecture directe de « grouper les segments qui se superposent physiquement » du cahier des charges.
  - Seuils par défaut : `SWIM_LENGTH_WARNING_THRESHOLD_M = 1500` et le seuil `min_segment_length_m = 30` ne sont pas spécifiés numériquement dans le cahier des charges au-delà de « anormalement long » / « ~30 m » — choisis raisonnablement, à ajuster avec de vrais tracés.
- **Le numéro de course dans le nom de fichier GPX (`Course{N}_...`) n'a jamais besoin de correspondre à l'identifiant interne de la course en base.** L'import est scopé par course dès l'upload (dossier `data/uploads/course_<id>/`) : le numéro extrait du nom de fichier ne sert qu'à documenter l'origine du fichier côté organisateur. `backend/app/orga/routes.py::_run_import_preview` force `result.course = course_id` sur chaque résultat avant d'appeler `core.gpx_import.assemble_course`, y compris pour les fichiers dont le nom est totalement invalide (`result.course` vaudrait `None` sinon). Sans ce fix, un fichier au nom invalide était silencieusement exclu du contrôle d'assemblage au lieu de bloquer l'import (bogue trouvé via les tests, pas juste en relisant le code).
- **Import en deux temps (aperçu puis validation) sans re-upload** : les fichiers sont écrits sur disque dans `data/uploads/course_<id>/` dès le premier POST, et la validation relit ce même dossier plutôt que d'exiger un nouvel envoi — évite de devoir faire transiter les fichiers via la session ou une API JSON. Répond directement à l'exigence « écran de prévisualisation avant validation » du §4.
- **CRUD événement/courses en Jinja server-rendered classique** (pas de SPA/API JSON) : seule la carte a vraiment besoin de JS/Vue. Les formulaires standards restent plus simples à tester (`curl`) et suffisent largement pour un usage petite équipe. Le dashboard (`orga/index.html`) embarque juste la liste des courses en JSON dans un `<script type="application/json">` pour que le front sache quels `trace.geojson` aller chercher.

## Pièges rencontrés

- `maplibre-gl` 6.x n'a plus d'export par défaut (`import maplibregl from "maplibre-gl"` casse) — utiliser les exports nommés (`import { Map, NavigationControl, AttributionControl } from "maplibre-gl"`).
- `npm install` peut planter avec `Cannot read properties of null (reading 'edgesOut')` sur npm 10 + graphe de peerDependencies complexe (vitest 5 + ses peers optionnels) — voir décision ci-dessus.
- Les commandes lancées en arrière-plan (`&`) dans un même appel Bash ne survivent pas toujours si la commande qui les a lancées se termine en erreur — préférer `nohup ... & disown` dans un appel dédié pour un serveur de dev qu'on veut garder actif entre plusieurs commandes.

## Commandes utiles

```bash
# Backend
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
FLASK_APP=backend/wsgi.py PYTHONPATH=backend .venv/bin/python -m flask run

# Créer un compte orga (base locale backend/data/app.db, créée automatiquement)
FLASK_APP=backend/wsgi.py PYTHONPATH=backend .venv/bin/flask create-user

# Tests / lint backend
.venv/bin/pytest backend/tests
.venv/bin/ruff check backend

# Régénérer le jeu de GPX de démo (backend/data/demo/)
PYTHONPATH=backend .venv/bin/python backend/scripts/generate_demo_gpx.py

# Frontend
cd frontend
npm install
npm run build     # génère backend/app/static/dist/ (manifest inclus)
npm run dev        # serveur Vite avec proxy /api -> Flask (nécessite VITE_DEV_SERVER=1 côté Flask, pas encore branché de bout en bout)
```

## Prochaines étapes (P3)

- Modèle de calcul TypeScript (fonctions pures, testées Vitest) : `timeline(course, profil)`, `distanceAt(course, profil, t)`, calcul de la « plage » entre premier et dernier coureur.
- Allures par course (saisie manuelle, validation premier < dernier sur chaque discipline) — pas encore dans le modèle `Course` (P2 n'a que nom/couleur/heure de départ), à ajouter.
- Horloge de simulation (store Pinia partagé), lecture/pause, vitesses ×1 à ×120, barre de défilement.
- Rendu de la plage sur la carte (bande épaisse semi-transparente, `lineSliceAlong`), marqueurs tête/queue de peloton, panneau latéral par course.
- Cas de test de référence à valider : tronçon Run 1000 m à 5:00/km puis Swim 200 m à 2:00/100 m → position à 1050 m après 6 min.
- Plus tard : premier déploiement réel sur PythonAnywhere (compte à créer/fournir côté utilisateur), et intégration du logo/captures dans `docs/brand/` pour extraire une vraie palette (actuellement palette provisoire, pas encore posée).
