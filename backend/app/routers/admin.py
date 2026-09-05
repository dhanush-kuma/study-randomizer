import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..core.rate_limit import limiter
from ..core.security import ROLE_ADMIN, create_access_token, get_current_admin, revoke_token
from ..database import get_db
from ..models import Admin
from ..schemas import AdminInfo, LoginRequest, LoginResponse, MessageResponse

router = APIRouter(prefix="/admin", tags=["admin"])

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 24


@router.get("/me", response_model=AdminInfo)
def get_me(
    response: Response,
    current_admin: Admin = Depends(get_current_admin),
):
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    return AdminInfo(username=current_admin.username, csrf_token=csrf_token)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    admin = db.query(Admin).filter(Admin.username == payload.username).first()
    if not admin or not bcrypt.checkpw(
        payload.password.encode(), admin.password_hash.encode()
    ):
        audit(
            "admin.login.failed",
            username=payload.username,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(admin.username, ROLE_ADMIN)
    set_auth_cookie(response, COOKIE_NAME, token, COOKIE_MAX_AGE)
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    audit(
        "admin.login.success",
        username=admin.username,
        ip=request.client.host if request.client else None,
    )
    return LoginResponse(message="Login successful.", csrf_token=csrf_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    revoke_token(access_token, db)
    clear_auth_cookie(response, COOKIE_NAME)
    clear_csrf_cookie(response)
    audit("admin.logout", username=current_admin.username)
    return MessageResponse(message="Logged out successfully.")
