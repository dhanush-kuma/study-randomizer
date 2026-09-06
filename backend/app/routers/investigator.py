from datetime import datetime, timezone
import bcrypt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import func
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
from ..models import Investigator, RandomizationRecord, Study
from ..schemas import (
    AssignKitRequest,
    ChangePasswordRequest,
    InvestigatorInfo,
    InvestigatorLoginRequest,
    LoginResponse,
    MessageResponse,
    RandomizationRecordOut,
    UnblindResponse,
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
def get_me(
    response: Response,
    current_investigator: Investigator = Depends(get_current_investigator),
    db: Session = Depends(get_db),
):
    study = db.query(Study).filter(Study.id == current_investigator.study_id).first()
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    return InvestigatorInfo(
        id=current_investigator.id,
        username=current_investigator.username,
        email=current_investigator.email,
        name=current_investigator.name,
        study_id=current_investigator.study_id,
        trial_id=study.protocol_code if study else "",
        study_title=study.title if study else None,
        study_description=study.description if study else None,
        blinding_type=study.blinding_type if study else "Double-Blind",
        emergency_unblinding_allowed=study.emergency_unblinding_allowed if study else True,
        status=current_investigator.status,
        csrf_token=csrf_token,
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


@router.post("/assign-kit", response_model=RandomizationRecordOut)
@limiter.limit("30/minute")
def assign_kit(
    request: Request,
    payload: AssignKitRequest,
    db: Session = Depends(get_db),
    current_investigator: Investigator = Depends(get_current_investigator),
):
    patient_id = payload.patient_id.strip()
    if not patient_id:
        raise HTTPException(status_code=400, detail="Patient ID is required.")

    study_id = current_investigator.study_id

    study = db.query(Study).filter(Study.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")

    # Check if patient_id is already assigned in this study
    existing = (
        db.query(RandomizationRecord)
        .filter(
            RandomizationRecord.study_id == study_id,
            func.lower(RandomizationRecord.assigned_patient_id) == patient_id.lower(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Patient ID '{patient_id}' has already been assigned a kit code in this study.",
        )

    # Get next unassigned record
    record = (
        db.query(RandomizationRecord)
        .filter(
            RandomizationRecord.study_id == study_id,
            RandomizationRecord.assigned_patient_id.is_(None),
        )
        .order_by(RandomizationRecord.sequence_number.asc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=400,
            detail="No unassigned kit codes remaining for this study.",
        )

    record.assigned_patient_id = patient_id
    record.assigned_by_investigator_id = current_investigator.id
    record.assigned_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(record)

    audit(
        "investigator.kit_assigned",
        investigator_id=current_investigator.id,
        study_id=study_id,
        patient_id=patient_id,
        kit_code=record.kit_code,
        sequence_number=record.sequence_number,
        ip=request.client.host if request.client else None,
    )

    return RandomizationRecordOut(
        id=record.id,
        study_id=record.study_id,
        sequence_number=record.sequence_number,
        kit_code=record.kit_code,
        treatment_name=record.treatment_name,
        assigned_patient_id=record.assigned_patient_id,
        assigned_by_investigator_id=record.assigned_by_investigator_id,
        assigned_by_investigator_username=current_investigator.username,
        assigned_at=record.assigned_at,
        blind=record.blind,
    )


@router.get("/assignments", response_model=list[RandomizationRecordOut])
def get_assignments(
    db: Session = Depends(get_db),
    current_investigator: Investigator = Depends(get_current_investigator),
):
    records = (
        db.query(RandomizationRecord)
        .filter(
            RandomizationRecord.study_id == current_investigator.study_id,
            RandomizationRecord.assigned_by_investigator_id == current_investigator.id,
            RandomizationRecord.assigned_patient_id.isnot(None),
        )
        .order_by(RandomizationRecord.assigned_at.desc())
        .all()
    )
    res = []
    for r in records:
        res.append(
            RandomizationRecordOut(
                id=r.id,
                study_id=r.study_id,
                sequence_number=r.sequence_number,
                kit_code=r.kit_code,
                treatment_name=r.treatment_name,
                assigned_patient_id=r.assigned_patient_id,
                assigned_by_investigator_id=r.assigned_by_investigator_id,
                assigned_by_investigator_username=r.assigned_by_investigator.username if r.assigned_by_investigator else None,
                assigned_at=r.assigned_at,
                blind=r.blind,
            )
        )
    return res


@router.post("/records/{record_id}/unblind", response_model=UnblindResponse)
def unblind_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_investigator: Investigator = Depends(get_current_investigator),
):
    record = (
        db.query(RandomizationRecord)
        .filter(
            RandomizationRecord.id == record_id,
            RandomizationRecord.study_id == current_investigator.study_id,
            RandomizationRecord.assigned_by_investigator_id == current_investigator.id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Assigned record not found.")

    study = db.query(Study).filter(Study.id == current_investigator.study_id).first()
    if not study or not study.emergency_unblinding_allowed:
        raise HTTPException(
            status_code=403,
            detail="Emergency unblinding is disabled for this study.",
        )

    record.blind = False
    db.commit()
    db.refresh(record)

    audit(
        "investigator.emergency_unblinded",
        investigator_id=current_investigator.id,
        study_id=study.id,
        record_id=record.id,
        patient_id=record.assigned_patient_id,
        treatment_name=record.treatment_name,
    )

    return UnblindResponse(
        record_id=record.id,
        treatment_name=record.treatment_name,
        message="Patient treatment arm unblinded successfully.",
    )


