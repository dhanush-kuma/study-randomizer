import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..core.rate_limit import limiter
from ..core.security import (
    ROLE_INVESTIGATOR,
    create_access_token,
    get_current_investigator,
    revoke_token,
)
from ..database import get_db
from ..models import Investigator, Study
from ..schemas import (
    ChangePasswordRequest,
    InvestigatorInfo,
    InvestigatorLoginRequest,
    LoginResponse,
    MessageResponse,
)

router = APIRouter(prefix="/investigator", tags=["investigator"])

COOKIE_NAME = "investigator_access_token"
COOKIE_MAX_AGE = 60 * 60 * 24


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: InvestigatorLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    # Resolve the study by trial_id (= protocol_code)
    study = db.query(Study).filter(Study.protocol_code == payload.trial_id.strip()).first()
    if not study:
        audit(
            "investigator.login.failed",
            trial_id=payload.trial_id,
            reason="study_not_found",
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid trial ID, username, or password.")

    # Find the investigator by (study_id, username) — username is unique within a study
    investigator = (
        db.query(Investigator)
        .filter(
            Investigator.study_id == study.id,
            Investigator.username == payload.username.strip(),
        )
        .first()
    )

    if not investigator or not bcrypt.checkpw(
        payload.password.encode(), investigator.password_hash.encode()
    ):
        audit(
            "investigator.login.failed",
            trial_id=payload.trial_id,
            username=payload.username,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid trial ID, username, or password.")

    if investigator.status == "revoked":
        audit(
            "investigator.login.failed",
            trial_id=payload.trial_id,
            username=payload.username,
            reason="revoked",
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Your access to this study has been revoked.")

    # Promote inactive → active on first login
    if investigator.status == "inactive":
        investigator.status = "active"
        db.commit()

    # JWT sub stores the investigator's DB id (study-unique usernames would collide across studies)
    token = create_access_token(str(investigator.id), ROLE_INVESTIGATOR)
    set_auth_cookie(response, COOKIE_NAME, token, COOKIE_MAX_AGE)
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    audit(
        "investigator.login.success",
        investigator_id=investigator.id,
        trial_id=payload.trial_id,
        username=investigator.username,
        ip=request.client.host if request.client else None,
    )
    return LoginResponse(message="Login successful.", csrf_token=csrf_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    investigator_access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
    current_investigator: Investigator = Depends(get_current_investigator),
):
    revoke_token(investigator_access_token, db)
    clear_auth_cookie(response, COOKIE_NAME)
    clear_csrf_cookie(response)
    audit("investigator.logout", investigator_id=current_investigator.id)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=InvestigatorInfo)
def get_me(current_investigator: Investigator = Depends(get_current_investigator)):
    return InvestigatorInfo(
        id=current_investigator.id,
        username=current_investigator.username,
        email=current_investigator.email,
        name=current_investigator.name,
        study_id=current_investigator.study_id,
        status=current_investigator.status,
    )


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("5/minute")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_investigator: Investigator = Depends(get_current_investigator),
):
    if not bcrypt.checkpw(
        payload.current_password.encode(), current_investigator.password_hash.encode()
    ):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_hash = bcrypt.hashpw(payload.new_password.encode(), bcrypt.gensalt()).decode()
    current_investigator.password_hash = new_hash
    db.commit()
    audit("investigator.password_changed", investigator_id=current_investigator.id)
    return MessageResponse(message="Password changed successfully.")
