import bcrypt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import SETUP_TOKEN_HEADER, verify_setup_token
from ..core.audit import audit
from ..core.rate_limit import limiter
from ..database import get_db
from ..models import Admin
from ..schemas import HealthResponse, SetupRequest, SetupResponse, StatusResponse

router = APIRouter(tags=["setup"])


@router.get("/", response_model=HealthResponse)
def health_check():
    """Public health check without exposing setup state."""
    return HealthResponse(status="ok", message="Study Randomizer API")


@router.get("/setup/status", response_model=StatusResponse)
@limiter.limit("10/minute")
def setup_status(
    request: Request,
    db: Session = Depends(get_db),
    setup_token: str | None = Header(default=None, alias=SETUP_TOKEN_HEADER),
):
    """Check whether initial setup is required. Requires a valid setup token."""
    try:
        verify_setup_token(setup_token)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    admin_exists = db.query(Admin).first() is not None
    if admin_exists:
        return StatusResponse(initialized=True, message="System is ready.")
    return StatusResponse(
        initialized=False,
        message="No admin account found. Please complete the initial setup.",
    )


@router.post("/setup", response_model=SetupResponse)
@limiter.limit("3/minute")
def setup_admin(
    request: Request,
    payload: SetupRequest,
    db: Session = Depends(get_db),
):
    """Create the first admin account. Requires a valid setup token."""
    try:
        verify_setup_token(payload.setup_token or None)
    except ValueError as exc:
        audit("setup.failed", reason="invalid_token", ip=request.client.host if request.client else None)
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if db.query(Admin).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Setup already completed. An admin account already exists.",
        )

    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    admin = Admin(username=payload.username.strip(), password_hash=hashed)
    db.add(admin)
    db.commit()

    audit(
        "setup.completed",
        username=admin.username,
        ip=request.client.host if request.client else None,
    )
    return SetupResponse(success=True, message="Admin account created successfully.")
