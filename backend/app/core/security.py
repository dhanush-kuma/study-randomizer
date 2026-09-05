import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from ..config import SECRET_KEY
from ..database import get_db
from ..models import Admin, Investigator, Organizer, RevokedToken

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
ROLE_ADMIN = "admin"
ROLE_ORGANIZER = "organizer"
ROLE_INVESTIGATOR = "investigator"


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": username,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def is_token_revoked(jti: str, db: Session) -> bool:
    return db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None


def revoke_token(token: str | None, db: Session) -> None:
    if not token:
        return
    payload = decode_token(token)
    if not payload:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    if is_token_revoked(jti, db):
        return
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()


def _resolve_user(
    token: str | None,
    expected_role: str,
    db: Session,
) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if payload.get("role") != expected_role:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    jti = payload.get("jti")
    if not jti or is_token_revoked(jti, db):
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return {"username": username}


def get_current_admin(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Admin:
    user = _resolve_user(access_token, ROLE_ADMIN, db)
    admin = db.query(Admin).filter(Admin.username == user["username"]).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found.")
    return admin


def get_current_organizer(
    organizer_access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Organizer:
    user = _resolve_user(organizer_access_token, ROLE_ORGANIZER, db)
    organizer = (
        db.query(Organizer).filter(Organizer.username == user["username"]).first()
    )
    if not organizer:
        raise HTTPException(status_code=401, detail="Organizer not found.")
    if not organizer.is_active:
        raise HTTPException(status_code=401, detail="Organizer account is deactivated.")
    return organizer


def get_current_investigator(
    investigator_access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> Investigator:
    """
    Resolve the currently authenticated investigator from the session cookie.
    The JWT `sub` stores the investigator's database id (as a string).
    """
    user = _resolve_user(investigator_access_token, ROLE_INVESTIGATOR, db)
    investigator = db.query(Investigator).filter(
        Investigator.id == int(user["username"])
    ).first()
    if not investigator:
        raise HTTPException(status_code=401, detail="Investigator not found.")
    if investigator.status == "revoked":
        raise HTTPException(status_code=401, detail="Investigator access has been revoked.")
    return investigator
