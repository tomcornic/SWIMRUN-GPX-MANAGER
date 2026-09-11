import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "app.db"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    VITE_DEV_SERVER = os.environ.get("VITE_DEV_SERVER", "") == "1"
    VITE_DEV_SERVER_URL = os.environ.get("VITE_DEV_SERVER_URL", "http://127.0.0.1:5173")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}"
    )
    UPLOADS_DIR = BACKEND_DIR / "data" / "uploads"
    PUBLISHED_DIR = BACKEND_DIR / "data" / "published"
