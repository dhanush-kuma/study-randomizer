import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Admin
from ..schemas import AdminInfo, LoginRequest, MessageResponse
from ..core.security import create_access_token, get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours in seconds


@router.get("/me", response_model=AdminInfo)
def get_me(current_admin: Admin = Depends(get_current_admin)):
    """Return the currently logged-in admin's info. 401 if not authenticated."""
    return AdminInfo(username=current_admin.username)


@router.post("/login", response_model=MessageResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Verify credentials and set an HTTP-only JWT cookie."""
    admin = db.query(Admin).filter(Admin.username == payload.username).first()
    if not admin or not bcrypt.checkpw(
        payload.password.encode(), admin.password_hash.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_access_token(admin.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
    )
    return MessageResponse(message="Login successful.")


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    """Clear the JWT cookie."""
    response.delete_cookie(key=COOKIE_NAME, samesite="lax")
    return MessageResponse(message="Logged out successfully.")
