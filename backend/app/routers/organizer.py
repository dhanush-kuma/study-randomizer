import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..config import email_is_configured
from ..core.email import send_study_invitation
from ..core.invitations import (
    generate_invitation_token,
    get_study_for_organizer,
    invitation_expires_at,
)
from ..core.rate_limit import limiter
from ..core.security import (
    ROLE_ORGANIZER,
    create_access_token,
    get_current_organizer,
    revoke_token,
)
from ..database import get_db
from ..models import Organizer, Study, StudyInvitation, TreatmentArm
from ..schemas import (
    InvitationOut,
    InviteDoctorRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    OrganizerInfo,
    StudyCreate,
    StudyOut,
)

router = APIRouter(prefix="/organizer", tags=["organizer"])

COOKIE_NAME = "organizer_access_token"
COOKIE_MAX_AGE = 60 * 60 * 24


@router.get("/me", response_model=OrganizerInfo)
def get_me(current_organizer: Organizer = Depends(get_current_organizer)):
    return OrganizerInfo(username=current_organizer.username)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    organizer = (
        db.query(Organizer).filter(Organizer.username == payload.username).first()
    )
    if not organizer or not bcrypt.checkpw(
        payload.password.encode(), organizer.password_hash.encode()
    ):
        audit(
            "organizer.login.failed",
            username=payload.username,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not organizer.is_active:
        audit("organizer.login.failed", username=payload.username, reason="deactivated")
        raise HTTPException(status_code=401, detail="Organizer account is deactivated.")

    token = create_access_token(organizer.username, ROLE_ORGANIZER)
    set_auth_cookie(response, COOKIE_NAME, token, COOKIE_MAX_AGE)
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    audit(
        "organizer.login.success",
        username=organizer.username,
        ip=request.client.host if request.client else None,
    )
    return LoginResponse(message="Login successful.", csrf_token=csrf_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    organizer_access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    revoke_token(organizer_access_token, db)
    clear_auth_cookie(response, COOKIE_NAME)
    clear_csrf_cookie(response)
    audit("organizer.logout", username=current_organizer.username)
    return MessageResponse(message="Logged out successfully.")


@router.post("/studies/", response_model=StudyOut, status_code=201)
def create_study(
    payload: StudyCreate,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
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
        random_seed=None,
        block_size_rules=payload.block_size_rules.strip()
        if payload.block_size_rules
        else None,
        emergency_unblinding_allowed=payload.emergency_unblinding_allowed,
        status="Draft",
    )
    db.add(study)
    db.flush()

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
    audit(
        "study.created",
        study_id=study.id,
        protocol_code=study.protocol_code,
        organizer=current_organizer.username,
    )
    return study


@router.get("/studies/", response_model=list[StudyOut])
def list_studies(
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    return (
        db.query(Study)
        .filter(Study.organizer_id == current_organizer.id)
        .order_by(Study.created_at.desc())
        .all()
    )


@router.get("/studies/{study_id}", response_model=StudyOut)
def get_study(
    study_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    return get_study_for_organizer(study_id, current_organizer.id, db)


@router.get("/studies/{study_id}/invitations", response_model=list[InvitationOut])
def list_invitations(
    study_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    get_study_for_organizer(study_id, current_organizer.id, db)
    return (
        db.query(StudyInvitation)
        .filter(StudyInvitation.study_id == study_id)
        .order_by(StudyInvitation.created_at.desc())
        .all()
    )


@router.post("/studies/{study_id}/invitations", response_model=InvitationOut, status_code=201)
@limiter.limit("10/hour")
def invite_doctor(
    request: Request,
    study_id: int,
    payload: InviteDoctorRequest,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    study = get_study_for_organizer(study_id, current_organizer.id, db)

    pending = (
        db.query(StudyInvitation)
        .filter(
            StudyInvitation.study_id == study_id,
            StudyInvitation.email == payload.email,
            StudyInvitation.status == "pending",
        )
        .first()
    )

    if pending:
        pending.token = generate_invitation_token()
        pending.expires_at = invitation_expires_at()
        pending.full_name = payload.full_name.strip() if payload.full_name else pending.full_name
        invitation = pending
    else:
        invitation = StudyInvitation(
            study_id=study_id,
            email=payload.email,
            full_name=payload.full_name.strip() if payload.full_name else None,
            token=generate_invitation_token(),
            status="pending",
            invited_by_organizer_id=current_organizer.id,
            expires_at=invitation_expires_at(),
        )
        db.add(invitation)

    db.flush()
    db.refresh(invitation)

    try:
        send_study_invitation(
            to_email=invitation.email,
            doctor_name=invitation.full_name,
            study_title=study.title,
            protocol_code=study.protocol_code,
            invitation_token=invitation.token,
        )
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.commit()
    db.refresh(invitation)
    audit(
        "invitation.sent",
        study_id=study_id,
        email=invitation.email,
        organizer=current_organizer.username,
        ip=request.client.host if request.client else None,
        email_configured=email_is_configured(),
    )
    return invitation
