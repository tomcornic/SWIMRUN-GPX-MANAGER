import json

from flask import current_app, render_template, send_from_directory

from app.public import bp


def _meta_publiee() -> dict | None:
    meta_path = current_app.config["PUBLISHED_DIR"] / "meta.json"
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text())


@bp.route("/")
def index():
    """Coquille HTML + point de montage Vue. Toutes les données de parcours sont
    chargées côté navigateur depuis /publie/*.json (jamais depuis la base) — le
    site public fonctionne même si le module orga est en cours de modification.

    Seules les métadonnées de partage (Open Graph) sont lues côté serveur ici,
    à partir du même meta.json statique : ça reste la lecture d'un fichier publié,
    pas un accès à la base.
    """
    meta = _meta_publiee()
    return render_template("public/index.html", meta=meta)


@bp.route("/publie/<path:filename>")
def fichier_publie(filename: str):
    response = send_from_directory(current_app.config["PUBLISHED_DIR"], filename)
    response.headers["Cache-Control"] = "public, max-age=300"
    return response
