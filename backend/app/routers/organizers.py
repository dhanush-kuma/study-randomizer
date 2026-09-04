import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.audit import audit
from ..core.security import get_current_admin
from ..database import get_db
from ..models import Admin, Organizer
from ..schemas import CreateOrganizerRequest, OrganizerOut

router = APIRouter(prefix="/admin/organizers", tags=["organizers"])


@router.post("/", response_model=OrganizerOut, status_code=201)
def create_organizer(
    payload: CreateOrganizerRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    existing = db.query(Organizer).filter(
        Organizer.username == payload.username.strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Username '{payload.username}' is already taken.",
        )

    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    organizer = Organizer(
        username=payload.username.strip(),
        password_hash=hashed,
        is_active=True,
    )
    db.add(organizer)
    db.commit()
    db.refresh(organizer)
    audit(
        "organizer.created",
        organizer=organizer.username,
        admin=current_admin.username,
    )
    return organizer


@router.get("/", response_model=list[OrganizerOut])
def list_organizers(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return db.query(Organizer).order_by(Organizer.created_at.desc()).all()


@router.patch("/{organizer_id}/status", response_model=OrganizerOut)
def toggle_organizer_status(
    organizer_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    organizer = db.query(Organizer).filter(Organizer.id == organizer_id).first()
    if not organizer:
        raise HTTPException(status_code=404, detail="Organizer not found.")

    organizer.is_active = not organizer.is_active
    db.commit()
    db.refresh(organizer)
    audit(
        "organizer.status_changed",
        organizer=organizer.username,
        is_active=organizer.is_active,
        admin=current_admin.username,
    )
    return organizer
