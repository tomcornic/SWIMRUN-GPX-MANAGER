# Swimrun de Saint-Pabu

Deux outils pour l'organisation du Swimrun de Saint-Pabu (Finistère) :

- **`/orga`** — simulateur privé (flux de coureurs, sécurité, logistique).
- **`/`** — site parcours public (repérage du tracé pour les participants).

Cahier des charges complet : `prompt-claude-code-swimrun-stpabu.md`. Avancement et décisions techniques : `CLAUDE.md`.

## Installation locale

### Backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

Ceci génère `backend/app/static/dist/` (bundles + `manifest.json`), lu par Flask pour injecter les bonnes URLs de scripts/styles.

### Lancer le serveur

```bash
FLASK_APP=backend/wsgi.py PYTHONPATH=backend .venv/bin/python -m flask run
```

Puis ouvrir `http://127.0.0.1:5000/` (site public) et `http://127.0.0.1:5000/orga/` (simulateur).

### Développement frontend avec rechargement à chaud

```bash
cd frontend
npm run dev
```

Sert les modules directement depuis Vite (proxy `/api` → `http://127.0.0.1:5000`). Nécessite de relancer Flask avec `VITE_DEV_SERVER=1` pour que les templates pointent vers le serveur Vite plutôt que le manifest de build.

## Déploiement sur PythonAnywhere

> Non encore exécuté à ce stade du projet — étapes documentées pour quand le compte PythonAnywhere sera prêt.

1. **Build front en local** : `cd frontend && npm run build`, puis commit du dossier `backend/app/static/dist/` (il est versionné, pas ignoré par Git — voir §2 du cahier des charges : pas de build CPU côté PA).
2. **Récupération du code** sur PythonAnywhere : `git pull` dans une console Bash PA, puis création du virtualenv :
   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r backend/requirements.txt
   ```
   (adapter la version Python à ce que propose le compte — voir `help.pythonanywhere.com/pages/PythonVersions`).
3. **Fichier WSGI** : dans l'onglet *Web* de PythonAnywhere, pointer le fichier WSGI généré vers `backend/wsgi.py` (`application = app`, à adapter selon le nom attendu par PA — le fichier expose déjà `app`).
4. **Mapping des fichiers statiques** : dans l'onglet *Web*, ajouter une entrée *Static files* : URL `/static/` → chemin `.../backend/app/static/`, pour qu'ils soient servis directement sans passer par Flask.
5. **Variables d'environnement** : définir `SECRET_KEY` (ne jamais la versionner) dans l'onglet *Web* (section *Environment variables*) ou dans le fichier WSGI. Créer la base SQLite et le premier compte orga via la commande CLI `flask create-user` (à implémenter en P2).
6. **Recharger la web app** (bouton *Reload* de l'onglet *Web*) puis vérifier :
   - `/` et `/orga/` répondent en `200`.
   - La carte satellite IGN s'affiche (vérifier que le serveur PA autorise bien les appels sortants du **navigateur** vers `data.geopf.fr` — aucun appel sortant n'est fait côté Python, donc pas de souci avec la restriction réseau de PA).
   - Les fichiers statiques (`/static/dist/...`) sont servis avec un `200` et le bon `content-type`.

## Qualité

```bash
# Backend
.venv/bin/pytest backend/tests
.venv/bin/ruff check backend

# Frontend
cd frontend
npm run lint
npm run test
```
