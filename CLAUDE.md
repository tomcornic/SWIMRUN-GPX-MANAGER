# CLAUDE.md — Swimrun de Saint-Pabu

Contexte complet du projet : voir `prompt-claude-code-swimrun-stpabu.md` à la racine (cahier des charges, stack imposée, plan de phases).

## État d'avancement

- **P0 en cours** : squelette Flask + Vite multi-pages, carte satellite IGN affichée sur `/` et `/orga`.
  - ✅ Dépôt Git initialisé (local uniquement, pas de remote).
  - ✅ Backend Flask : `create_app()`, blueprints `orga` (`/orga`) et `public` (`/`), helper `vite_asset()` pour lire le manifest Vite.
  - ✅ Frontend Vite multi-pages (`orga` + `public`), MapLibre GL JS avec fond IGN orthophotos (WMTS, sans clé), Pinia initialisé (pas encore de store).
  - ✅ Build front testé, deux pages testées en local (`curl` + vérification directe de la tuile WMTS).
  - ⏳ Déploiement PythonAnywhere réel : **reporté** à la demande de l'utilisateur. Code et README prêts, mais pas encore déployé.

## Décisions techniques et justification

- **Cible Python locale = 3.11-compatible**, même si la machine de dev a Python 3.14 installé. Raison : PythonAnywhere gratuit propose 3.11/3.12/3.13 selon la date de création du compte — éviter toute syntaxe post-3.11 pour ne pas se faire piéger au déploiement.
- **Versions des dépendances front figées à jour au 2026-09-11** (vue 3.5.42, maplibre-gl 6.9.0, vite 8.3.0, vue-tsc 3.3.11, typescript 5.9.3) plutôt qu'aux versions initialement supposées — un premier `npm install` a révélé un décalage important avec les versions attendues. **`vitest` est volontairement figé en `^4.1.11`** (pas la 5.x) : la 5.x fait planter `npm@10.8.2` (bug arborist connu, `Cannot read properties of null (reading 'edgesOut')`) et on ne peut pas monter npm 12 sans Node ≥22 (on a Node 20.20.2 en local). À réévaluer si l'environnement Node change.
- **Manifest Vite** : avec Vite 8, `manifest.json` est généré dans `dist/.vite/manifest.json` (pas à la racine de `dist/`). Le helper `backend/app/vite.py` lit ce chemin.
- **CSS des chunks partagés** : `orga` et `public` importent tous les deux `shared/map.ts`, donc Rollup les fusionne dans un chunk commun (`map-*.js` / `map-*.css`) au lieu de dupliquer le CSS dans chaque entrée. Le helper `vite_asset()` doit donc parcourir récursivement les `imports` du manifest pour retrouver tout le CSS associé — un premier essai qui ne lisait que `chunk.css` de l'entrée oubliait le CSS de MapLibre (la carte s'affichait sans son CSS). Corrigé.
- **WMTS IGN orthophotos** : URL KVP validée en conditions réelles (tuile récupérée et affichée pour Saint-Pabu, voir ci-dessous) :
  `https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&TILEMATRIXSET=PM_0_19&LAYER=ORTHOIMAGERY.ORTHOPHOTOS&STYLE=normal&FORMAT=image/jpeg&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}`
  Pas de clé requise. Fallback Esri (§2 du cahier des charges) pas encore implémenté — prévu quand le sélecteur de fond de carte sera construit (P6/P7).
- **`node --check`** est autorisé sans confirmation dans `.claude/settings.json` (vérif de syntaxe seule, sans exécution).

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

# Frontend
cd frontend
npm install
npm run build     # génère backend/app/static/dist/ (manifest inclus)
npm run dev        # serveur Vite avec proxy /api -> Flask (nécessite VITE_DEV_SERVER=1 côté Flask, pas encore branché de bout en bout)
```

## Prochaines étapes (P1)

- `core/filenames.py`, `core/gpx_import.py`, `core/geometry.py`, `core/overlaps.py` : parsing des noms `Course{N}_Tronçon{M}_{Run|Swim}.gpx` (NFC avant regex), lecture/assemblage des GPX, détection des passages multiples.
- Générer un jeu de GPX synthétiques réalistes autour de Saint-Pabu (48.565 N, 4.596 W) — décidé avec l'utilisateur en attendant les vrais fichiers.
- Tests pytest sur tracé aller-retour et boucle en « 8 ».
- Quand prêt côté utilisateur : premier déploiement réel sur PythonAnywhere (compte à créer/fournir), et intégration du logo/captures dans `docs/brand/` pour extraire une vraie palette (actuellement palette provisoire, pas encore posée).
