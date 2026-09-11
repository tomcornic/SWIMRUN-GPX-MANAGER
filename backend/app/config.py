import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    VITE_DEV_SERVER = os.environ.get("VITE_DEV_SERVER", "") == "1"
    VITE_DEV_SERVER_URL = os.environ.get("VITE_DEV_SERVER_URL", "http://127.0.0.1:5173")
