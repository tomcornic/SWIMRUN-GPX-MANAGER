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
2. **Récupération du code** sur PythonAnywhere : dans une console Bash PA, `git clone` (ou `git pull` si déjà cloné) le dépôt dans le *home* du compte (ex. `/home/<utilisateur>/swimrun_stpab2026.0.0`), puis création du virtualenv :
   ```bash
   cd ~/swimrun_stpab2026.0.0
   python3.12 -m venv .venv
   .venv/bin/pip install -r backend/requirements.txt
   ```
   (adapter la version Python à ce que propose le compte — voir `help.pythonanywhere.com/pages/PythonVersions` — et rester cohérent avec la version utilisée en local, cf. `CLAUDE.md`).
3. **App web** : onglet *Web* → *Add a new web app* → *Manual configuration* (surtout pas *Flask*, qui régénère un projet à sa façon) → choisir la même version Python que le virtualenv. Renseigner :
   - **Virtualenv** : `/home/<utilisateur>/swimrun_stpab2026.0.0/.venv`
   - **Fichier WSGI** (PA fournit un chemin du type `/var/www/<utilisateur>_pythonanywhere_com_wsgi.py`, à éditer intégralement — tout son contenu par défaut est à remplacer) :
     ```python
     import sys

     project_root = "/home/<utilisateur>/swimrun_stpab2026.0.0"
     backend_dir = project_root + "/backend"
     for path in (project_root, backend_dir):
         if path not in sys.path:
             sys.path.insert(0, path)

     from wsgi import app as application  # backend/wsgi.py expose `app`, PA attend `application`
     ```
     (`backend_dir` doit être sur `sys.path` pour que `backend/wsgi.py` puisse faire `from app import create_app` — c'est l'équivalent WSGI du `PYTHONPATH=backend` utilisé en local.)
4. **Mapping des fichiers statiques** : dans l'onglet *Web*, section *Static files*, ajouter une entrée URL `/static/` → chemin `/home/<utilisateur>/swimrun_stpab2026.0.0/backend/app/static/`, pour qu'ils soient servis directement sans passer par Flask/le worker WSGI.
5. **Variables d'environnement** : section *Environment variables* de l'onglet *Web*, définir `SECRET_KEY` (une valeur aléatoire, ne jamais la versionner — sans cette variable l'app démarre quand même mais avec la valeur de secours `dev-only-change-me` de `backend/app/config.py`, à ne surtout pas laisser en production). La base SQLite (`backend/data/app.db`) se crée automatiquement au premier lancement ; créer le premier compte orga avec, dans une console Bash PA :
   ```bash
   cd ~/swimrun_stpab2026.0.0
   FLASK_APP=backend/wsgi.py PYTHONPATH=backend .venv/bin/flask create-user
   ```
6. **Recharger la web app** (bouton *Reload* de l'onglet *Web*) puis vérifier :
   - `/` et `/orga/login` répondent en `200` (une erreur WSGI donne en général une page `Something went wrong :-(` — le détail de l'exception est dans le lien *Error log* de l'onglet *Web*, la cause la plus fréquente étant un `sys.path` incomplet à l'étape 3).
   - La carte satellite IGN s'affiche (vérifier que le serveur PA autorise bien les appels sortants du **navigateur** vers `data.geopf.fr` — aucun appel sortant n'est fait côté Python, donc pas de souci avec la restriction réseau de PA, qui ne s'applique qu'aux requêtes émises depuis le serveur lui-même).
   - Les fichiers statiques (`/static/dist/...`) sont servis avec un `200` et le bon `content-type` (`text/css`, `application/javascript`, `font/woff2`) — sinon revérifier le mapping de l'étape 4.
   - Connexion sur `/orga/login` avec le compte créé à l'étape 5, puis déconnexion, pour confirmer que les sessions/cookies fonctionnent bien sous le domaine `*.pythonanywhere.com`.

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
