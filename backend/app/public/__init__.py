from flask import Blueprint, render_template

bp = Blueprint("public", __name__, url_prefix="")


@bp.route("/")
def index():
    return render_template("public/index.html")
