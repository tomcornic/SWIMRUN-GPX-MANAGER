from flask import Flask

from app.cli import register_cli
from app.config import Config
from app.extensions import csrf, db, login_manager
from app.vite import register_vite


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "orga.login"
    login_manager.login_message = "Merci de vous connecter pour accéder à cette page."

    register_vite(app)
    register_cli(app)

    from app.orga import bp as orga_bp
    from app.public import bp as public_bp

    app.register_blueprint(orga_bp)
    app.register_blueprint(public_bp)

    from app import models  # noqa: F401  (enregistre les modèles auprès de SQLAlchemy)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(models.User, int(user_id))

    with app.app_context():
        app.config["UPLOADS_DIR"].mkdir(parents=True, exist_ok=True)
        db.create_all()

    return app
