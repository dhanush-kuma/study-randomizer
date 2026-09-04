import os
import secrets
from pathlib import Path

from fastapi import Response

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

DEFAULT_SECRET_KEY = "change-this-secret-key-in-production"

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@127.0.0.1/study-randomizer",
)

SECRET_KEY = os.environ.get("SECRET_KEY", DEFAULT_SECRET_KEY)
SETUP_TOKEN = os.environ.get("SETUP_TOKEN", "")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
COOKIE_SAMESITE = os.environ.get("COOKIE_SAMESITE", "lax")
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SETUP_TOKEN_HEADER = "X-Setup-Token"

if IS_PRODUCTION:
    if not SECRET_KEY or SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set to a strong value in production.")
    if not SETUP_TOKEN:
        raise RuntimeError("SETUP_TOKEN must be set in production.")


def verify_setup_token(token: str | None) -> None:
    """Raise ValueError when the setup token is missing or invalid."""
    if not SETUP_TOKEN:
        if IS_PRODUCTION:
            raise ValueError("Setup is disabled.")
        return
    if not token or not secrets.compare_digest(token, SETUP_TOKEN):
        raise ValueError("Invalid setup token.")


def set_auth_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        max_age=max_age,
    )


def clear_auth_cookie(response: Response, key: str) -> None:
    response.delete_cookie(key=key, samesite=COOKIE_SAMESITE, secure=COOKIE_SECURE)


def set_csrf_cookie(response: Response, max_age: int) -> str:
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
        max_age=max_age,
    )
    return token


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        samesite=COOKIE_SAMESITE,
        secure=COOKIE_SECURE,
    )
