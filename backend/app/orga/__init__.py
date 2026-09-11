from flask import Blueprint, render_template

bp = Blueprint("orga", __name__, url_prefix="/orga")


@bp.route("/")
def index():
    return render_template("orga/index.html")
