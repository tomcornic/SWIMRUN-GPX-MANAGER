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
  - ✅ Affichage des tracés : endpoint `/orga/courses/<id>/trace.geojson`, rendu sur la carte MapLibre du dashboard (remplacé en P3 par un rendu plus riche, voir ci-dessous — `trace.geojson` reste utilisé tel quel).
  - ✅ 45 tests pytest verts (auth, CRUD événement/courses, flux d'import complet avec les GPX de démo de P1, y compris réimport et rejet sur erreur), `ruff check` propre.
  - ✅ Parcours complet revalidé sur un vrai serveur `flask run` (pas seulement le client de test) : login → événement → course → upload → aperçu → validation → `trace.geojson` → carte, plus vérification que les routes protégées redirigent bien sans session.
- **P3 terminé** : allures, moteur de simulation TypeScript pur, horloge partagée, lecture/pause, rendu de la plage sur la carte, panneau d'état.
  - ✅ Modèle `Course` étendu avec 4 allures (secondes, nullable) : `premier_allure_course_s`, `premier_allure_nage_s`, `dernier_allure_course_s`, `dernier_allure_nage_s`. Saisie en mm:ss via `core/pace.py` (parse/format), validation croisée premier < dernier dans `CourseForm.validate()`.
  - ✅ Endpoint `/orga/courses/<id>/simulation.json` : troncons (numéro/type/longueur), allures (ou `null` si incomplètes), tracé complet — tout ce dont le moteur TS a besoin en un seul appel.
  - ✅ `frontend/src/orga/simulation.ts` : `timeline()`, `distanceAt()`, `plageAt()`, `tronconActuel()`, `etatCoureur()`, `validerAllure()` — fonctions pures, aucune dépendance DOM/Flask.
  - ✅ **Cas de référence du cahier des charges validé** : tronçon Run 1000 m à 5:00/km + Swim 200 m à 2:00/100 m → 1050 m exactement à t = 6 min (`simulation.test.ts`).
  - ✅ 28 tests Vitest verts (`simulation.test.ts` + `temps.test.ts`), en plus des 59 tests pytest (7 nouveaux sur les allures/`simulation.json`).
  - ✅ Store Pinia `horloge` (temps courant, bornes, lecture/pause, vitesse ×1 à ×120) et `courses` (charge `simulation.json` de chaque course, calcule les bornes globales `[premier départ − 15 min ; dernière arrivée + 15 min]`).
  - ✅ `ControlesLecture.vue` (lecture/pause, vitesse, horloge HH:MM:SS, saut à une heure précise, raccourci espace) et `PanneauCourse.vue` (état, km tête/queue, tronçon en cours, étalement) par course.
  - ✅ `carte-simulation.ts` : plage rendue en bande semi-transparente via `@turf/line-slice-along`, marqueurs tête/queue via `@turf/along`, tracés de base avec tronçons de natation en pointillé.
  - ⚠️ **Non vérifié visuellement** : aucun outil de navigateur n'était disponible dans cette session. Le payload API, le calcul pur (Vitest) et la compilation TypeScript sont validés ; le rendu carte réel (fluidité de l'animation, alignement visuel de la plage) reste à confirmer à l'œil par l'utilisateur.
- **P4 terminé** : module marée (saisie, interpolation en cosinus, graphique synchronisé).
  - ✅ `core/tides.py` : `interpoler_cosinus()` (formule exacte du §5), `tendance()`, `echantillonner()` (toutes les 5 min), `convertir_vers_utc()` (UTC / UTC+1 fixe / heure légale avec bascule été-hiver automatique via `zoneinfo`), `parser_csv()` (Option B). 24 tests pytest verts.
  - ✅ Modèle `MareeReleve` (event_id, moment_utc, hauteur_m, type `pm`/`bm`/`mesure`), toujours stocké en UTC.
  - ✅ Écran `/orga/maree` : Option A (formulaire point par point : date, heure, hauteur, PM/BM, fuseau source) et Option B (upload CSV `datetime;hauteur_m`, réimport qui remplace proprement les mesures CSV sans toucher aux extrêmes saisis en Option A — même logique de réimport « propre » qu'en P2 pour les tronçons).
  - ✅ Endpoint `/orga/maree/serie.json?debut_s=&fin_s=` : mêmes bornes (secondes depuis minuit Europe/Paris) que l'horloge de simulation, série échantillonnée + liste des extrêmes PM/BM, tout exprimé directement dans le référentiel `horloge.tempsS` pour que le front n'ait aucune conversion de fuseau à faire.
  - ✅ Store Pinia `maree` (`hauteurAt()`, `tendanceAt()` — interpolation linéaire entre échantillons 5 min, testées Vitest) et `GraphiqueMaree.vue` (Chart.js + chartjs-plugin-annotation, curseur vertical synchronisé sur `horloge.tempsS`, clic sur le graphique = `horloge.definirTemps()`, texte « Hauteur d'eau : X,XX m — marée montante/descendante »).
  - ✅ 91 tests pytest + 36 tests Vitest verts au total.
  - ✅ **Vérifié de bout en bout sur un vrai serveur `flask run`**, y compris les deux modes de saisie (Option A + Option B CSV, réimport sans doublon) et la cohérence chiffrée de l'interpolation : une mesure CSV saisie à 09:00 à 5,80 m ressort **exactement** à 5,80 m dans `serie.json` au même instant.
  - ⚠️ Comme en P3, le rendu du graphique lui-même (Chart.js dans le navigateur) n'a pas pu être vérifié visuellement — aucun outil navigateur disponible dans cette session.
- **P5 terminé** : POI (CRUD, clic carte, km auto) et publication du parcours en JSON public.
  - ✅ `core/geometry.py::project_point_onto_track()` : projection orthogonale d'un point sur un tracé (segment le plus proche, clampé aux extrémités) — utilisée pour le km automatique des POI. 5 nouveaux tests pytest.
  - ✅ Modèles `Poi` (type, nom, description, lat/lon, côté de passage) et `PoiCourse` (association POI↔course, avec `distance_m` recalculé à chaque sauvegarde).
  - ✅ Écran `/orga/poi` : CRUD complet, formulaire avec sélection multi-courses, placement par **clic sur une carte MapLibre dédiée** (`PoiMapPicker.vue`, marqueur déplaçable) qui remplit les champs lat/lon cachés — voir décision ci-dessous sur le montage conditionnel du bundle Vue.
  - ✅ `core/publish.py` : dataclasses `CoursePublic`/`TronconPublic`/`PoiPublic` (aucun champ d'allure — structurellement impossible d'y fuiter une donnée privée), `construire_meta()`, `construire_course_geojson()`, `construire_pois_json()`. 6 tests pytest, dont deux gardes-fous qui grep le JSON produit pour s'assurer qu'aucun mot-clé `allure`/`profil`/`simulation` n'apparaît.
  - ✅ Écran `/orga/publier` : génère `meta.json` + `course-{id}.geojson` (tracé, tronçons, passages multiples réutilisant `core/overlaps.detect_multiple_passages`) + `pois-{id}.json` par course dans `data/published/`, affiche la date de dernière publication.
  - ✅ 100 tests pytest + 36 tests Vitest verts au total.
  - ✅ **Vérifié de bout en bout sur un vrai serveur `flask run`** : un POI placé exactement sur le point de départ du tracé ressort à **0,00 km** ; publication déclenchée et **grep manuel confirmant l'absence totale** de « allure »/« profil »/« simulation » dans les 3 fichiers générés.
- **P6 terminé** : site public — carte, tronçons distincts, flèches, passages multiples, slider kilométrique, POI, mobile-first.
  - ✅ Backend : `GET /` (coquille HTML + OG tags lus depuis `meta.json` publié, jamais depuis la DB) et `GET /publie/<fichier>` qui sert `data/published/` directement (`send_from_directory`, cache 5 min). Favicon copié depuis `docs/brand/logo.jpg` vers `static/img/favicon.jpg`. 5 tests pytest.
  - ✅ **Bug d'isolation des tests corrigé** : `conftest.py` ne surchargeait pas `PUBLISHED_DIR`, donc certains tests lisaient le vrai `backend/data/published/` du disque au lieu d'un dossier temporaire isolé — trouvé par un test P6 qui échouait de façon non déterministe selon l'état laissé par les sessions manuelles précédentes. Corrigé, et complété par `test_publier_route.py` (la route `/orga/publier` elle-même n'avait jamais eu de test pytest jusqu'ici, seulement testée manuellement en curl en P5).
  - ✅ `shared/map.ts` : commutateur satellite/plan (`definirFondCarte`, fond OSM ajouté) — la fonctionnalité restait différée depuis P0. Fonction `segmentsParType` extraite de l'orga vers `shared/` (découpage tracé/tronçons par lineSliceAlong, maintenant utilisée par l'orga *et* le public).
  - ✅ `public/parcours.ts` (types + fetch de `meta.json`/`course-{id}.geojson`/`pois-{id}.json`, avec `?v=genere_le` pour le cache HTTP) et `public/navigation.ts` (fonctions pures : `tronconALaDistance`, `prochainPoi`, `passageActifA`, `messagePassage`) — 13 tests Vitest.
  - ✅ `public/carte-parcours.ts` : liseré blanc sous le tracé, tronçons course/nage distincts, flèches directionnelles (icône SVG en `icon-image`, pas de police de glyphes externe nécessaire — voir décision ci-dessous), passages multiples décalés (`line-offset`) avec pastilles numérotées, marqueurs POI cliquables (emoji par type, DOM `Marker`), marqueur de position suivant `turf.along`.
  - ✅ Store Pinia `parcours` (course active, distance courante, chargement) et composants `SelecteurCourse`/`SliderKm`/`EncartInfo`/`PanneauPoi`/`LegendeParcours`. Bouton lecture automatique (défilement à vitesse fixe), bascule satellite/plan.
  - ✅ 104 tests pytest + 49 tests Vitest verts au total.
  - ✅ **Vérifié de bout en bout sur un vrai serveur `flask run`**, avec le jeu de démo Course 2 qui contient un vrai aller-retour : `course-1.geojson` publié contient bien `passages_multiples` avec les bonnes bornes en mètres, `/` et `/publie/*.json` répondent 200 **sans aucune session** (site public réellement public), tags Open Graph corrects.
  - ⚠️ Comme en P3-P5, le rendu visuel réel (carte, flèches, décalage des passages, slider, bottom sheet mobile) n'a pas pu être vérifié dans un navigateur — aucun outil navigateur disponible dans cette session. C'est la partie la plus à risque de cette phase : la géométrie (offsets, turf.along) est testée numériquement mais jamais vue.

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
- **CRUD événement/courses en Jinja server-rendered classique** (pas de SPA/API JSON) : seule la carte a vraiment besoin de JS/Vue. Les formulaires standards restent plus simples à tester (`curl`) et suffisent largement pour un usage petite équipe. Le dashboard (`orga/index.html`) embarque juste la liste des courses en JSON dans un `<script type="application/json">` pour que le front sache quels `trace.geojson`/`simulation.json` aller chercher.
- **Vocabulaire du domaine gardé en français dans le code** (tronçon, allure, plage, orga...), contrairement à la règle 6 du cahier des charges (« code en anglais ») prise au pied de la lettre. **Décision explicite de l'utilisateur** après que l'écart a été signalé : le vocabulaire métier reste français partout (comme dans le cahier des charges lui-même), seuls les termes génériques (get/create/list, structure du code) sont en anglais. S'applique à tout le code déjà écrit (P0-P2, non modifié) et à tout le code à venir.
- **`étalement` du peloton (panneau d'état, §5)** : le cahier des charges demande un étalement « en mètres et en minutes » sans formule. Implémenté comme : mètres = distance tête − distance queue ; minutes = ce même écart en mètres divisé par l'allure *du dernier coureur sur son tronçon courant*. C'est une approximation raisonnable (pas une mesure physique exacte, puisque premier et dernier n'ont pas la même allure), à ajuster si l'utilisateur préfère une autre définition une fois testé en vrai.
- **Boucle d'animation `requestAnimationFrame` tourne en continu**, indépendamment de l'état lecture/pause (`horloge.avancer()` ne fait rien si `enLecture` est faux, mais `mettreAJourCarte()` s'exécute quand même à chaque frame). Volontaire : permet à la carte de refléter immédiatement un déplacement manuel du curseur ou un saut d'heure, même à l'arrêt, sans logique de dirty-checking séparée. Le coût (quelques appels Turf par course et par frame) est négligeable pour 3 courses.
- **`verbatimModuleSyntax` de TypeScript** (activé via `@vue/tsconfig`) exige `import type { ... }` pour tout ce qui n'est que des types (ex. `CircleLayerSpecification`, `LineLayerSpecification` de maplibre-gl) — sinon `vue-tsc -b` échoue avec `TS1484`. Séparer systématiquement les imports de valeurs et de types quand une bibliothèque mélange les deux dans le même module.
- **Une seule fonction d'interpolation cosinus pour les deux modes de saisie** (Option A extrêmes PM/BM et Option B mesures CSV brutes) : le cahier des charges n'annonce la formule cosinus qu'« (Option A) », mais rien n'empêche mathématiquement de l'appliquer aussi entre deux mesures CSV consécutives — c'est juste moins physiquement motivé (l'ease-in/out a du sens entre deux extrêmes réels, moins entre deux mesures arbitraires rapprochées). Simplification assumée pour ne pas maintenir deux algorithmes d'interpolation ; `MareeReleve.type` distingue quand même `pm`/`bm`/`mesure` pour que seuls les vrais extrêmes soient marqués sur le graphique.
- **`serie.json` reçoit `debut_s`/`fin_s` en « secondes depuis minuit Europe/Paris »** (le référentiel déjà utilisé par `horloge.tempsS` et `Course.start_time`), pas des timestamps UTC. Le backend fait toute la conversion de fuseau (combine `Event.date` + les secondes, localise en heure légale, convertit en UTC pour interroger les `MareeReleve`), et renvoie la série déjà réexprimée dans ce même référentiel de secondes locales. Le front n'a donc aucune arithmétique de fuseau horaire à faire — juste tracer `secondes` en x.
- **Montage Vue conditionnel dans `orga/main.ts`** : jusqu'à P4, le bundle `orga` ne montait qu'une seule app sur `#app` (le dashboard). P5 ajoute un second point de montage (`#poi-map-app`, une mini-app `PoiMapPicker.vue` juste pour capter un clic sur la carte) sur une page Jinja différente (`poi_form.html`) qui n'a pas de `#app`. Plutôt que créer un 3ᵉ point d'entrée Vite (rebuild du chunk `map` partagé, complexité de build en plus), `main.ts` teste la présence de chaque élément racine et monte l'app correspondante — un seul bundle, deux apps Vue indépendantes selon la page. Le picker écrit directement dans les `<input>` cachés du formulaire Jinja (par `id`, passé en `data-*`) plutôt que de chercher à faire du data-binding Vue↔Jinja.
- **Km des POI recalculé à chaque sauvegarde, pas mis en cache autrement qu'en base** : `PoiCourse.distance_m` est réécrit à chaque création/modification d'un POI (toutes les lignes `poi_courses` du POI sont supprimées puis recréées). Pas de recalcul automatique si le tracé GPX d'une course est réimporté après coup — un POI existant garde son ancien km jusqu'à ce qu'on le modifie. Acceptable en V1 (réimporter une course après avoir placé des POI dessus est un cas rare), mais à surveiller si ça devient gênant à l'usage.
- **Flèches directionnelles en `icon-image` (SVG chargé en data URI), pas en `text-field`** : MapLibre a besoin d'un serveur de glyphes (police SDF) configuré dans le style pour rendre du texte/emoji en couche `symbol` — je n'en ai pas configuré (ça aurait ajouté une dépendance à un service de fonts externe, contraire à l'esprit « pas d'appel à une API externe »). Une icône image (chargée via `map.loadImage` + `map.addImage`) n'a pas ce besoin et suffit pour une flèche simple. Les marqueurs POI (emoji) et les pastilles de passage utilisent des `maplibregl.Marker` avec élément DOM personnalisé plutôt que des couches `symbol` — même raison, et ça permet un `onClick` natif sans configurer d'interactivité de couche GL.
- **`vite_asset()` et les CSS de composants scoped ne s'appliquent pas aux marqueurs DOM créés dynamiquement** (`document.createElement`) : les styles `.marqueur-poi`/`.marqueur-position`/`.badge-passage` sont dans `public/marqueurs.css`, importé globalement dans `main.ts`, pas dans un `<style scoped>` de composant — les styles scoped Vue ne touchent que les éléments rendus par le template du composant, jamais des éléments créés à la main en JS.
- **Commutateur satellite/plan construit dans `shared/map.ts`** (couche OSM ajoutée, masquée par défaut) mais le **fallback automatique Esri en cas d'échec IGN reste non implémenté** — seul le commutateur manuel était explicitement requis pour P6 ; le fallback sur erreur est noté comme amélioration possible en finition (P7), pas bloquant pour « parcours lisible et navigable ».
- **Message de passage multiple générique**, pas le texte contextualisé de l'exemple du cahier des charges (« vous revenez vers la plage ») : je n'ai aucun moyen de déduire automatiquement la direction géographique narrative depuis les données. `messagePassage()` produit « 2ᵉ passage — portion empruntée 2 fois. », qui reste informatif sans inventer un contexte que je ne peux pas vérifier.

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
npm run test       # Vitest (simulation.ts, temps.ts, stores/maree.ts, public/navigation.ts...)
```

## Prochaines étapes (P7)

**C'est la dernière phase du plan (§10)** — thème, finitions responsive, performance, README de déploiement. Après P7, tout le périmètre fonctionnel V1 du cahier des charges est couvert (sous réserve de la vérification visuelle jamais faite, voir ci-dessous).

- **Vérification visuelle en navigateur — la vraie priorité avant tout le reste.** P3 à P6 ont été construites et testées (pytest/Vitest/curl) sans jamais être vues dans un navigateur. Avant de polir le thème, il faut d'abord confirmer que tout s'affiche et s'anime correctement : carte, plage, graphique de marée, slider, passages multiples décalés, bottom sheet mobile. Utiliser `claude-in-chrome` ou demander à l'utilisateur de tester et remonter ce qui ne va pas.
- Thème : extraire une palette depuis `docs/brand/logo.jpg` et `docs/brand/affiche.jpg` (script Python + Pillow, pas encore fait), proposer 2 variantes à l'utilisateur avant de les appliquer. Actuellement chaque page a ses couleurs codées en dur dans des `<style scoped>`/`_layout.html` — à terme, centraliser dans un seul fichier de variables CSS partagé (`shared/theme.css` ou équivalent), comme prévu au cahier des charges (§2 : « toutes les couleurs... passent par des variables CSS dans un fichier de thème unique »).
- Polices auto-hébergées (pas de CDN Google Fonts) — pas encore choisies.
- Finitions responsive desktop pour l'orga (actuellement pensé pour un usage bureau simple, pas testé sur mobile — normal, c'est le site public qui est mobile-first).
- Performance du site public : bundle minimal (actuellement le chunk `map` partagé fait ~1,1 Mo à cause de maplibre-gl — envisager le code-splitting signalé par Vite si ça pose un problème réel sur réseau mobile faible), JSON compacts (déjà raisonnablement petits), cache HTTP (déjà en place via `?v=genere_le` + `Cache-Control`).
- README de déploiement PythonAnywhere (§9) — actuellement dans `README.md` mais jamais exécuté en vrai (déploiement reporté depuis P0 à la demande de l'utilisateur).
- Quand prêt côté utilisateur : premier déploiement réel (compte PythonAnywhere à créer/fournir).
