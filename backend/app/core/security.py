from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Admin

# ── Config ─────────────────────────────────────────────────────────────────
# TODO: move to env var before deploying
SECRET_KEY = "change-this-secret-key-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


# ── Token helpers ───────────────────────────────────────────────────────────
def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str | None:
    """Return username from token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── Dependency ──────────────────────────────────────────────────────────────
def get_current_admin(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Admin:
    """FastAPI dependency — resolves the logged-in Admin or raises 401."""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    username = decode_token(access_token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found.")
    return admin
