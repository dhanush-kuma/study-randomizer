import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Doctor, Study, StudyDoctor, StudyInvitation

INVITATION_EXPIRE_DAYS = 7


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)


def get_study_for_organizer(study_id: int, organizer_id: int, db: Session) -> Study:
    study = (
        db.query(Study)
        .filter(Study.id == study_id, Study.organizer_id == organizer_id)
        .first()
    )
    if not study:
        raise HTTPException(status_code=404, detail="Study not found.")
    return study


def get_valid_invitation(token: str, db: Session) -> StudyInvitation:
    invitation = (
        db.query(StudyInvitation).filter(StudyInvitation.token == token).first()
    )
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    if invitation.status == "accepted":
        raise HTTPException(status_code=409, detail="Invitation has already been accepted.")

    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail=f"Invitation is {invitation.status}.")

    if invitation.expires_at <= _utcnow():
        invitation.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired.")

    return invitation


def accept_invitation(invitation: StudyInvitation, doctor: Doctor, db: Session) -> None:
    if doctor.email.lower() != invitation.email.lower():
        raise HTTPException(
            status_code=403,
            detail="This invitation was sent to a different email address.",
        )

    existing = (
        db.query(StudyDoctor)
        .filter(
            StudyDoctor.study_id == invitation.study_id,
            StudyDoctor.doctor_id == doctor.id,
        )
        .first()
    )
    if existing:
        invitation.status = "accepted"
        invitation.doctor_id = doctor.id
        invitation.accepted_at = _utcnow()
        db.commit()
        return

    db.add(
        StudyDoctor(
            study_id=invitation.study_id,
            doctor_id=doctor.id,
        )
    )
    invitation.status = "accepted"
    invitation.doctor_id = doctor.id
    invitation.accepted_at = _utcnow()
    db.commit()


def invitation_expires_at() -> datetime:
    return _utcnow() + timedelta(days=INVITATION_EXPIRE_DAYS)
