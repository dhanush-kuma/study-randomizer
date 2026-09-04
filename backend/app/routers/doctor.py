import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..core.email import send_study_invitation
from ..core.invitations import (
    accept_invitation,
    generate_invitation_token,
    get_study_for_organizer,
    get_valid_invitation,
    invitation_expires_at,
)
from ..core.rate_limit import limiter
from ..core.security import (
    ROLE_DOCTOR,
    create_access_token,
    get_current_doctor,
    revoke_token,
)
from ..database import get_db
from ..models import Doctor, Study, StudyDoctor, StudyInvitation
from ..schemas import (
    DoctorInfo,
    DoctorSignupRequest,
    DoctorStudyOut,
    InvitationPreview,
    LoginRequest,
    LoginResponse,
    MessageResponse,
)

router = APIRouter(prefix="/doctor", tags=["doctor"])

COOKIE_NAME = "doctor_access_token"
COOKIE_MAX_AGE = 60 * 60 * 24


@router.get("/invitations/{token}", response_model=InvitationPreview)
def preview_invitation(token: str, db: Session = Depends(get_db)):
    invitation = get_valid_invitation(token, db)
    study = db.query(Study).filter(Study.id == invitation.study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")

    account_exists = (
        db.query(Doctor).filter(Doctor.email == invitation.email.lower()).first()
        is not None
    )

    return InvitationPreview(
        email=invitation.email,
        full_name=invitation.full_name,
        study_title=study.title,
        protocol_code=study.protocol_code,
        expires_at=invitation.expires_at,
        account_exists=account_exists,
    )


@router.post("/signup", response_model=LoginResponse)
@limiter.limit("5/minute")
def signup(
    request: Request,
    payload: DoctorSignupRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    invitation = get_valid_invitation(payload.token, db)

    if db.query(Doctor).filter(Doctor.email == invitation.email.lower()).first():
        raise HTTPException(
            status_code=409,
            detail="An account already exists for this email. Please log in to accept the invitation.",
        )

    if db.query(Doctor).filter(Doctor.username == payload.username.strip()).first():
        raise HTTPException(status_code=409, detail="Username is already taken.")

    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    full_name = payload.full_name.strip() if payload.full_name else invitation.full_name
    doctor = Doctor(
        email=invitation.email.lower(),
        username=payload.username.strip(),
        password_hash=hashed,
        full_name=full_name.strip() if full_name else None,
    )
    db.add(doctor)
    db.flush()

    accept_invitation(invitation, doctor, db)

    token = create_access_token(doctor.username, ROLE_DOCTOR)
    set_auth_cookie(response, COOKIE_NAME, token, COOKIE_MAX_AGE)
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    audit(
        "doctor.signup",
        username=doctor.username,
        email=doctor.email,
        study_id=invitation.study_id,
        ip=request.client.host if request.client else None,
    )
    return LoginResponse(message="Account created successfully.", csrf_token=csrf_token)


@router.post("/invitations/{token}/accept", response_model=MessageResponse)
def accept_invitation_route(
    token: str,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    invitation = get_valid_invitation(token, db)
    accept_invitation(invitation, current_doctor, db)
    audit(
        "doctor.invitation.accepted",
        username=current_doctor.username,
        study_id=invitation.study_id,
    )
    return MessageResponse(message="You have joined the study.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    doctor = db.query(Doctor).filter(Doctor.username == payload.username).first()
    if not doctor or not bcrypt.checkpw(
        payload.password.encode(), doctor.password_hash.encode()
    ):
        audit(
            "doctor.login.failed",
            username=payload.username,
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not doctor.is_active:
        raise HTTPException(status_code=401, detail="Doctor account is deactivated.")

    token = create_access_token(doctor.username, ROLE_DOCTOR)
    set_auth_cookie(response, COOKIE_NAME, token, COOKIE_MAX_AGE)
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    audit(
        "doctor.login.success",
        username=doctor.username,
        ip=request.client.host if request.client else None,
    )
    return LoginResponse(message="Login successful.", csrf_token=csrf_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    doctor_access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    revoke_token(doctor_access_token, db)
    clear_auth_cookie(response, COOKIE_NAME)
    clear_csrf_cookie(response)
    audit("doctor.logout", username=current_doctor.username)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=DoctorInfo)
def get_me(current_doctor: Doctor = Depends(get_current_doctor)):
    return DoctorInfo(
        username=current_doctor.username,
        email=current_doctor.email,
        full_name=current_doctor.full_name,
    )


@router.get("/studies/", response_model=list[DoctorStudyOut])
def list_studies(
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor),
):
    rows = (
        db.query(StudyDoctor, Study)
        .join(Study, StudyDoctor.study_id == Study.id)
        .filter(StudyDoctor.doctor_id == current_doctor.id)
        .order_by(StudyDoctor.joined_at.desc())
        .all()
    )
    return [
        DoctorStudyOut(
            id=study.id,
            title=study.title,
            protocol_code=study.protocol_code,
            status=study.status,
            blinding_type=study.blinding_type,
            joined_at=membership.joined_at,
        )
        for membership, study in rows
    ]
