import pytest

from app import create_app
from app.config import Config
from app.extensions import db as _db
from app.models import User


@pytest.fixture
def app(tmp_path):
    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        UPLOADS_DIR = tmp_path / "uploads"
        PUBLISHED_DIR = tmp_path / "published"
        WTF_CSRF_ENABLED = False

    flask_app = create_app(TestConfig)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_credentials():
    return {"email": "orga@example.com", "password": "secret123"}


@pytest.fixture
def user(app, user_credentials):
    with app.app_context():
        u = User(email=user_credentials["email"])
        u.set_password(user_credentials["password"])
        _db.session.add(u)
        _db.session.commit()
        return u.id


@pytest.fixture
def logged_in_client(client, user, user_credentials):
    client.post("/orga/login", data=user_credentials)
    return client
