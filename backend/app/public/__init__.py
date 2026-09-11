from flask import Blueprint

bp = Blueprint("public", __name__, url_prefix="")

from app.public import routes  # noqa: E402,F401
