import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Organizer, Study, TreatmentArm
from ..schemas import (
    LoginRequest,
    MessageResponse,
    OrganizerInfo,
    StudyCreate,
    StudyOut,
)
from ..core.security import create_access_token, get_current_organizer

router = APIRouter(prefix="/organizer", tags=["organizer"])


COOKIE_NAME = "organizer_access_token"
COOKIE_MAX_AGE = 60 * 60 * 24  # 24 hours in seconds


@router.get("/me", response_model=OrganizerInfo)
def get_me(current_organizer: Organizer = Depends(get_current_organizer)):
    """Return the currently logged-in organizer's info. 401 if not authenticated."""
    return OrganizerInfo(username=current_organizer.username)


@router.post("/login", response_model=MessageResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Verify organizer credentials and set an HTTP-only JWT cookie."""
    organizer = (
        db.query(Organizer).filter(Organizer.username == payload.username).first()
    )
    if not organizer or not bcrypt.checkpw(
        payload.password.encode(), organizer.password_hash.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not organizer.is_active:
        raise HTTPException(status_code=401, detail="Organizer account is deactivated.")

    token = create_access_token(organizer.username)
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
    """Clear the organizer JWT cookie."""
    response.delete_cookie(key=COOKIE_NAME, samesite="lax")
    return MessageResponse(message="Logged out successfully.")


# ── Study Management ───────────────────────────────────────────────────────

@router.post("/studies/", response_model=StudyOut, status_code=201)
def create_study(
    payload: StudyCreate,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """Create a new study managed by the authenticated organizer."""
    existing = (
        db.query(Study)
        .filter(Study.protocol_code == payload.protocol_code.strip())
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Study with protocol code '{payload.protocol_code}' already exists.",
        )

    study = Study(
        organizer_id=current_organizer.id,
        title=payload.title.strip(),
        protocol_code=payload.protocol_code.strip(),
        description=payload.description.strip() if payload.description else None,
        blinding_type=payload.blinding_type,
        target_sample_size=payload.target_sample_size,
        randomization_method=payload.randomization_method,
        random_seed=payload.random_seed.strip() if payload.random_seed else None,
        block_size_rules=payload.block_size_rules.strip()
        if payload.block_size_rules
        else None,
        emergency_unblinding_allowed=payload.emergency_unblinding_allowed,
        status="Draft",  # Initial status is always Draft until randomization schedule exists
    )
    db.add(study)
    db.flush()  # assign study.id

    for arm_data in payload.treatment_arms:
        arm = TreatmentArm(
            study_id=study.id,
            name=arm_data.name.strip(),
            short_code=arm_data.short_code.strip(),
            allocation_ratio=arm_data.allocation_ratio,
            description=arm_data.description.strip() if arm_data.description else None,
        )
        db.add(arm)

    db.commit()
    db.refresh(study)
    return study



@router.get("/studies/", response_model=list[StudyOut])
def list_studies(
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """List all studies belonging to the authenticated organizer."""
    return (
        db.query(Study)
        .filter(Study.organizer_id == current_organizer.id)
        .order_by(Study.created_at.desc())
        .all()
    )

