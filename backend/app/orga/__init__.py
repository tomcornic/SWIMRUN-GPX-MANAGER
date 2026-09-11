from flask import Blueprint

bp = Blueprint("orga", __name__, url_prefix="/orga")

from app.orga import routes  # noqa: E402,F401
