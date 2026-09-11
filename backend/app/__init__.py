from flask import Flask

from app.config import Config
from app.vite import register_vite


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    register_vite(app)

    from app.orga import bp as orga_bp
    from app.public import bp as public_bp

    app.register_blueprint(orga_bp)
    app.register_blueprint(public_bp)

    return app
