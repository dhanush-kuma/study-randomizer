import math
from typing import Optional
import bcrypt
from fastapi import APIRouter, Cookie, Depends, File, HTTPException, Query, Request, Response, UploadFile
from sqlalchemy import String, cast, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..config import clear_auth_cookie, clear_csrf_cookie, set_auth_cookie, set_csrf_cookie
from ..core.audit import audit
from ..config import email_is_configured
from ..core.investigator_invite import (
    DuplicateInvestigatorError,
    create_and_send_investigator_invite,
    parse_investigator_csv,
)
from ..core.randomization_csv import parse_randomization_csv
from ..core.randomization_engine import generate_sequence
from ..core.investigators import generate_temp_password
from ..core.email import send_investigator_credentials
from ..core.rate_limit import limiter
from ..core.security import (
    ROLE_ORGANIZER,
    create_access_token,
    get_current_organizer,
    revoke_token,
)
from ..database import get_db
from ..models import Investigator, Organizer, RandomizationRecord, Study, TreatmentArm
from ..schemas import (
    BulkInviteResponse,
    BulkInviteRowResult,
    CsvUploadResponse,
    ArmCount,
    GenerateRandomizationRequest,
    GenerateRandomizationResponse,
    InviteInvestigatorRequest,
    InvestigatorOut,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    OrganizerInfo,
    PaginatedRandomizationRecords,
    RandomizationRecordOut,
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

    if study.status == "Active":
        locked_fields = {"randomization_method", "block_size_min", "block_size_max", "target_sample_size"}
        if any(k in payload.model_dump(exclude_unset=True) for k in locked_fields):
            raise HTTPException(
                status_code=400,
                detail="Study is Active and locked. Randomization settings cannot be modified.",
            )

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

    if study.status == "Active":
        raise HTTPException(
            status_code=400,
            detail="Study is Active and locked. Treatment arms cannot be modified.",
        )

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


@router.post(
    "/studies/{study_id}/investigators/{investigator_id}/reset-password",
    response_model=InvestigatorOut,
)
@limiter.limit("10/hour")
def reset_investigator_password(
    request: Request,
    study_id: int,
    investigator_id: int,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """
    Generate a new random password for the investigator, email it to them,
    and reset their status to 'inactive' (they must log in again).
    """
    study = _get_study_for_organizer(study_id, current_organizer.id, db)
    investigator = (
        db.query(Investigator)
        .filter(Investigator.id == investigator_id, Investigator.study_id == study_id)
        .first()
    )
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator not found.")
    if investigator.status == "revoked":
        raise HTTPException(
            status_code=409,
            detail="Cannot reset password for a revoked investigator. Restore their access first.",
        )

    new_password = generate_temp_password()
    investigator.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    # Reset to inactive so the next login is their first effective login
    investigator.status = "inactive"
    db.flush()

    try:
        send_investigator_credentials(
            to_email=investigator.email,
            name=investigator.name,
            study_title=study.title,
            protocol_code=study.protocol_code,
            username=investigator.username,
            temp_password=new_password,
        )
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    db.commit()
    db.refresh(investigator)
    audit(
        "investigator.password_reset",
        investigator_id=investigator.id,
        study_id=study_id,
        email=investigator.email,
        organizer=current_organizer.username,
        ip=request.client.host if request.client else None,
        email_configured=email_is_configured(),
    )
    return investigator


@router.post(
    "/studies/{study_id}/upload-randomization-csv",
    response_model=CsvUploadResponse,
)
@limiter.limit("20/hour")
async def upload_randomization_csv(
    request: Request,
    study_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """
    Upload a pre-randomized CSV sequence.  Replaces any existing
    randomization_records for the study and sets its status to 'Active'.

    Required CSV columns: sequence_number, kit_code, short_code
    Optional column:      treatment_arm  (display name; falls back to short_code)
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    study = _get_study_for_organizer(study_id, current_organizer.id, db)

    if study.status == "Active":
        raise HTTPException(
            status_code=400,
            detail="Study is Active and locked. Sequence records have already been finalized.",
        )

    content = await file.read()
    try:
        parsed_rows = parse_randomization_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Replace all existing randomization records for this study
    db.query(RandomizationRecord).filter(
        RandomizationRecord.study_id == study_id
    ).delete()

    new_records: list[RandomizationRecord] = []
    for row in parsed_rows:
        record = RandomizationRecord(
            study_id=study_id,
            sequence_number=row["sequence_number"],
            kit_code=row["kit_code"],
            treatment_name=row["treatment_name"],
        )
        db.add(record)
        new_records.append(record)

    # Mark the study as active and note it was populated via CSV
    study.status = "Active"
    study.random_seed = "csv-upload"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while saving the randomization records.",
        )

    for record in new_records:
        db.refresh(record)

    audit(
        "study.randomization_csv_uploaded",
        study_id=study_id,
        inserted_count=len(new_records),
        organizer=current_organizer.username,
        ip=request.client.host if request.client else None,
    )

    return CsvUploadResponse(
        inserted_count=len(new_records),
        study_status=study.status,
        records=[RandomizationRecordOut.model_validate(r) for r in new_records],
    )


@router.get(
    "/studies/{study_id}/randomization-records",
    response_model=PaginatedRandomizationRecords,
)
def get_randomization_records(
    study_id: int,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """
    Get paginated randomization records for a study.
    Supports filtering by search query (kit_code, treatment_name, assigned_patient_id, sequence_number)
    and status_filter ('assigned' | 'unassigned').
    """
    study = _get_study_for_organizer(study_id, current_organizer.id, db)

    base_query = db.query(RandomizationRecord).filter(
        RandomizationRecord.study_id == study.id
    )

    query = base_query
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            or_(
                RandomizationRecord.kit_code.ilike(s),
                RandomizationRecord.treatment_name.ilike(s),
                RandomizationRecord.assigned_patient_id.ilike(s),
                cast(RandomizationRecord.sequence_number, String).ilike(s),
            )
        )

    if status_filter == "assigned":
        query = query.filter(RandomizationRecord.assigned_patient_id.isnot(None))
    elif status_filter == "unassigned":
        query = query.filter(RandomizationRecord.assigned_patient_id.is_(None))
    elif status_filter == "blinded":
        query = query.filter(RandomizationRecord.blind.is_(True))
    elif status_filter == "unblinded":
        query = query.filter(RandomizationRecord.blind.is_(False))

    total_count = query.count()

    assigned_count = base_query.filter(
        RandomizationRecord.assigned_patient_id.isnot(None)
    ).count()
    unassigned_count = base_query.filter(
        RandomizationRecord.assigned_patient_id.is_(None)
    ).count()
    blinded_count = base_query.filter(
        RandomizationRecord.blind.is_(True)
    ).count()
    unblinded_count = base_query.filter(
        RandomizationRecord.blind.is_(False)
    ).count()

    offset = (page - 1) * per_page
    records = (
        query.options(joinedload(RandomizationRecord.assigned_by_investigator))
        .order_by(RandomizationRecord.sequence_number.asc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    record_outs = []
    for r in records:
        inv_username = r.assigned_by_investigator.username if r.assigned_by_investigator else None
        record_outs.append(
            RandomizationRecordOut(
                id=r.id,
                study_id=r.study_id,
                sequence_number=r.sequence_number,
                kit_code=r.kit_code,
                treatment_name=r.treatment_name,
                assigned_patient_id=r.assigned_patient_id,
                assigned_by_investigator_id=r.assigned_by_investigator_id,
                assigned_by_investigator_username=inv_username,
                assigned_at=r.assigned_at,
                blind=r.blind,
            )
        )

    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    # Per-arm counts: total and assigned, using a single GROUP BY pass
    from sqlalchemy import case, func as sqlfunc

    arm_rows = (
        db.query(
            RandomizationRecord.treatment_name,
            sqlfunc.count(RandomizationRecord.id).label("total"),
            sqlfunc.count(
                case(
                    (RandomizationRecord.assigned_patient_id.isnot(None), 1),
                )
            ).label("assigned"),
        )
        .filter(RandomizationRecord.study_id == study.id)
        .group_by(RandomizationRecord.treatment_name)
        .order_by(RandomizationRecord.treatment_name.asc())
        .all()
    )
    arm_counts = [
        ArmCount(
            treatment_name=row.treatment_name,
            total=row.total,
            assigned=row.assigned,
            unassigned=row.total - row.assigned,
        )
        for row in arm_rows
    ]

    return PaginatedRandomizationRecords(
        total_count=total_count,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        assigned_count=assigned_count,
        unassigned_count=unassigned_count,
        blinded_count=blinded_count,
        unblinded_count=unblinded_count,
        arm_counts=arm_counts,
        records=record_outs,
    )


@router.post(
    "/studies/{study_id}/generate-randomization",
    response_model=GenerateRandomizationResponse,
    status_code=201,
)
@limiter.limit("10/hour")
def generate_randomization(
    request: Request,
    study_id: int,
    payload: GenerateRandomizationRequest,
    db: Session = Depends(get_db),
    current_organizer: Organizer = Depends(get_current_organizer),
):
    """
    Generate randomization records from the study's manual settings.
    Replaces any existing records and sets study status → Active.
    """
    study = _get_study_for_organizer(study_id, current_organizer.id, db)

    if study.status == "Active":
        raise HTTPException(
            status_code=400,
            detail="Study is already Active and locked. Randomization records cannot be regenerated.",
        )

    # Merge payload overrides with stored study settings
    n = payload.target_sample_size or study.target_sample_size
    method = payload.randomization_method or study.randomization_method
    block_min = payload.block_size_min if payload.block_size_min is not None else study.block_size_min
    block_max = payload.block_size_max if payload.block_size_max is not None else study.block_size_max
    seed = payload.random_seed  # None is fine – engine will auto-generate

    # Validation guards
    if not n or n < 1:
        raise HTTPException(
            status_code=400,
            detail="Target sample size must be set and be at least 1 before generating.",
        )

    valid_methods = {"Simple Random", "Permuted Block", "Minimization"}
    if method not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid randomization method '{method}'. Choose from: {', '.join(valid_methods)}.",
        )

    if method == "Permuted Block" and (block_min is None or block_min < 1):
        raise HTTPException(
            status_code=400,
            detail="Block size (min) must be set when using Permuted Block randomization.",
        )

    arms = (
        db.query(TreatmentArm)
        .filter(TreatmentArm.study_id == study_id)
        .order_by(TreatmentArm.id.asc())
        .all()
    )
    if not arms:
        raise HTTPException(
            status_code=400,
            detail="At least one treatment arm must be configured before generating randomization records.",
        )

    arms_data = [
        {
            "name": arm.name,
            "short_code": arm.short_code,
            "allocation_ratio": arm.allocation_ratio,
        }
        for arm in arms
    ]

    kit_prefix = study.protocol_code.upper().replace(" ", "-")

    try:
        records_data, seed_used = generate_sequence(
            arms=arms_data,
            n=n,
            kit_prefix=kit_prefix,
            method=method,
            block_size_min=block_min,
            block_size_max=block_max,
            seed=seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Persist: delete existing records first
    db.query(RandomizationRecord).filter(
        RandomizationRecord.study_id == study_id
    ).delete()

    new_records: list[RandomizationRecord] = []
    for row in records_data:
        record = RandomizationRecord(
            study_id=study_id,
            sequence_number=row["sequence_number"],
            kit_code=row["kit_code"],
            treatment_name=row["treatment_name"],
        )
        db.add(record)
        new_records.append(record)

    # Persist updated study settings + mark active
    study.target_sample_size = n
    study.randomization_method = method
    study.block_size_min = block_min
    study.block_size_max = block_max
    study.status = "Active"
    study.random_seed = str(seed_used)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while saving the randomization records.",
        )

    for record in new_records:
        db.refresh(record)

    audit(
        "study.randomization_generated",
        study_id=study_id,
        method=method,
        n=n,
        seed=seed_used,
        inserted_count=len(new_records),
        organizer=current_organizer.username,
        ip=request.client.host if request.client else None,
    )

    return GenerateRandomizationResponse(
        inserted_count=len(new_records),
        study_status=study.status,
        seed_used=seed_used,
        records=[RandomizationRecordOut.model_validate(r) for r in new_records],
    )
