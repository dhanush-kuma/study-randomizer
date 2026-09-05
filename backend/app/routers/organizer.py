import bcrypt
from fastapi import APIRouter, Cookie, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..config import email_is_configured
from ..core.investigator_invite import (
    DuplicateInvestigatorError,
    create_and_send_investigator_invite,
    parse_investigator_csv,
)
from ..core.rate_limit import limiter
from ..core.security import (
    ROLE_ORGANIZER,
    create_access_token,
    get_current_organizer,
    revoke_token,
)
from ..database import get_db
from ..models import Investigator, Organizer, Study, TreatmentArm
from ..schemas import (
    BulkInviteResponse,
    BulkInviteRowResult,
    InviteInvestigatorRequest,
    InvestigatorOut,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    OrganizerInfo,
    StudyCreate,
    StudyOut,
    StudyUpdate,
    TreatmentArmCreate,
    TreatmentArmOut,
)

router = APIRouter(prefix="/organizer", tags=["organizer"])

COOKIE_NAME = "organizer_access_token"
COOKIE_MAX_AGE = 60 * 60 * 24


def _get_study_for_organizer(study_id: int, organizer_id: int, db: Session) -> Study:
    """Return the study only if it belongs to the given organizer, else 404."""
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organizer_id == organizer_id)
        .first()
    )
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")
    return study


def _ensure_protocol_code_available(
    db: Session,
    protocol_code: str,
    *,
    exclude_study_id: int | None = None,
) -> None:
    """Ensure protocol_code is unique across all studies (system-wide, not per organizer)."""
    query = db.query(Study).filter(Study.protocol_code == protocol_code.strip())
    if exclude_study_id is not None:
        query = query.filter(Study.id != exclude_study_id)
    if query.first():
        raise HTTPException(
            status_code=409,
            detail=f"Study with protocol code '{protocol_code}' already exists.",
        )


@router.get("/me", response_model=OrganizerInfo)
def get_me(
    response: Response,
    current_organizer: Organizer = Depends(get_current_organizer),
):
    csrf_token = set_csrf_cookie(response, COOKIE_MAX_AGE)
    return OrganizerInfo(username=current_organizer.username, csrf_token=csrf_token)


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
    _ensure_protocol_code_available(db, payload.protocol_code)

    study = Study(
        organizer_id=current_organizer.id,
        title=payload.title.strip(),
        protocol_code=payload.protocol_code.strip(),
        description=payload.description.strip() if payload.description else None,
        blinding_type=payload.blinding_type,
        target_sample_size=payload.target_sample_size,
        randomization_method=payload.randomization_method,
        random_seed=None,
        block_size_min=payload.block_size_min,
        block_size_max=payload.block_size_max,
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

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Study with protocol code '{payload.protocol_code}' already exists.",
        ) from None
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
    return _get_study_for_organizer(study_id, current_organizer.id, db)


@router.patch("/studies/{study_id}", response_model=StudyOut)
def update_study(
    study_id: int,
    payload: StudyUpdate,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    study = _get_study_for_organizer(study_id, current_organizer.id, db)
    updates = payload.model_dump(exclude_unset=True)
    if "protocol_code" in updates and updates["protocol_code"] is not None:
        _ensure_protocol_code_available(
            db,
            updates["protocol_code"],
            exclude_study_id=study_id,
        )
        updates["protocol_code"] = updates["protocol_code"].strip()
    for field, value in updates.items():
        setattr(study, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        protocol_code = updates.get("protocol_code", study.protocol_code)
        raise HTTPException(
            status_code=409,
            detail=f"Study with protocol code '{protocol_code}' already exists.",
        ) from None
    db.refresh(study)
    audit("study.updated", study_id=study_id, organizer=current_organizer.username)
    return study


@router.post("/studies/{study_id}/arms", response_model=list[TreatmentArmOut], status_code=201)
def set_treatment_arms(
    study_id: int,
    payload: list[TreatmentArmCreate],
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    study = _get_study_for_organizer(study_id, current_organizer.id, db)

    # Replace all existing arms
    db.query(TreatmentArm).filter(TreatmentArm.study_id == study.id).delete()

    new_arms = []
    for arm_data in payload:
        arm = TreatmentArm(
            study_id=study.id,
            name=arm_data.name.strip(),
            short_code=arm_data.short_code.strip(),
            allocation_ratio=arm_data.allocation_ratio,
            description=arm_data.description.strip() if arm_data.description else None,
        )
        db.add(arm)
        new_arms.append(arm)

    db.commit()
    for arm in new_arms:
        db.refresh(arm)
    audit("study.arms.updated", study_id=study_id, count=len(new_arms), organizer=current_organizer.username)
    return new_arms

@router.get("/studies/{study_id}/investigators", response_model=list[InvestigatorOut])
def list_investigators(
    study_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """Return all investigators for the given study."""
    _get_study_for_organizer(study_id, current_organizer.id, db)
    return (
        db.query(Investigator)
        .filter(Investigator.study_id == study_id)
        .order_by(Investigator.created_at.desc())
        .all()
    )


@router.post("/studies/{study_id}/investigators", response_model=InvestigatorOut, status_code=201)
@limiter.limit("20/hour")
def invite_investigator(
    request: Request,
    study_id: int,
    payload: InviteInvestigatorRequest,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """
    Create an investigator record for this study with system-generated credentials
    and send the credentials to the provided email address.
    """
    study = _get_study_for_organizer(study_id, current_organizer.id, db)

    try:
        investigator = create_and_send_investigator_invite(
            study=study,
            email=payload.email,
            name=payload.name.strip() if payload.name else None,
            db=db,
        )
    except DuplicateInvestigatorError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.commit()
    db.refresh(investigator)
    audit(
        "investigator.invited",
        investigator_id=investigator.id,
        study_id=study_id,
        email=investigator.email,
        username=investigator.username,
        organizer=current_organizer.username,
        ip=request.client.host if request.client else None,
        email_configured=email_is_configured(),
    )
    return investigator


@router.post(
    "/studies/{study_id}/investigators/bulk",
    response_model=BulkInviteResponse,
)
@limiter.limit("10/hour")
async def bulk_invite_investigators(
    request: Request,
    study_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """Invite multiple investigators from a 2-column CSV (email, name), no header row."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    study = _get_study_for_organizer(study_id, current_organizer.id, db)
    content = await file.read()

    try:
        parsed_rows = parse_investigator_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    results: list[BulkInviteRowResult] = []
    seen_emails: set[str] = set()
    created_count = 0
    skipped_count = 0
    failed_count = 0

    for row_num, name, email in parsed_rows:
        if email in seen_emails:
            skipped_count += 1
            results.append(
                BulkInviteRowResult(
                    row=row_num,
                    email=email,
                    status="skipped",
                    message="Duplicate email in CSV.",
                )
            )
            continue
        seen_emails.add(email)

        try:
            investigator = create_and_send_investigator_invite(
                study=study,
                email=email,
                name=name,
                db=db,
            )
            db.commit()
            db.refresh(investigator)
            created_count += 1
            results.append(
                BulkInviteRowResult(
                    row=row_num,
                    email=email,
                    username=investigator.username,
                    status="created",
                )
            )
            audit(
                "investigator.invited",
                investigator_id=investigator.id,
                study_id=study_id,
                email=investigator.email,
                username=investigator.username,
                organizer=current_organizer.username,
                ip=request.client.host if request.client else None,
                email_configured=email_is_configured(),
                bulk=True,
            )
        except DuplicateInvestigatorError as exc:
            db.rollback()
            skipped_count += 1
            results.append(
                BulkInviteRowResult(
                    row=row_num,
                    email=email,
                    status="skipped",
                    message=str(exc),
                )
            )
        except RuntimeError as exc:
            db.rollback()
            failed_count += 1
            results.append(
                BulkInviteRowResult(
                    row=row_num,
                    email=email,
                    status="failed",
                    message=str(exc),
                )
            )
        except Exception:
            db.rollback()
            failed_count += 1
            results.append(
                BulkInviteRowResult(
                    row=row_num,
                    email=email,
                    status="failed",
                    message="Unexpected error while inviting investigator.",
                )
            )

    audit(
        "investigator.bulk_invited",
        study_id=study_id,
        organizer=current_organizer.username,
        created_count=created_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        ip=request.client.host if request.client else None,
    )

    return BulkInviteResponse(
        created_count=created_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        results=results,
    )


@router.patch(
    "/studies/{study_id}/investigators/{investigator_id}/revoke",
    response_model=InvestigatorOut,
)
def revoke_investigator(
    study_id: int,
    investigator_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """Revoke an investigator's access to the study."""
    _get_study_for_organizer(study_id, current_organizer.id, db)
    investigator = (
        db.query(Investigator)
        .filter(Investigator.id == investigator_id, Investigator.study_id == study_id)
        .first()
    )
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found.")
    if investigator.status == "revoked":
        raise HTTPException(status_code=409, detail="Investigator access is already revoked.")

    investigator.status = "revoked"
    db.commit()
    db.refresh(investigator)
    audit(
        "investigator.revoked",
        investigator_id=investigator.id,
        study_id=study_id,
        organizer=current_organizer.username,
    )
    return investigator


@router.patch(
    "/studies/{study_id}/investigators/{investigator_id}/restore",
    response_model=InvestigatorOut,
)
def restore_investigator(
    study_id: int,
    investigator_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """Restore a revoked investigator's access to the study."""
    _get_study_for_organizer(study_id, current_organizer.id, db)
    investigator = (
        db.query(Investigator)
        .filter(Investigator.id == investigator_id, Investigator.study_id == study_id)
        .first()
    )
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found.")
    if investigator.status != "revoked":
        raise HTTPException(status_code=409, detail="Investigator access is not revoked.")

    # inactive until they log in again; login promotes inactive → active
    investigator.status = "inactive"
    db.commit()
    db.refresh(investigator)
    audit(
        "investigator.restored",
        investigator_id=investigator.id,
        study_id=study_id,
        organizer=current_organizer.username,
    )
    return investigator
