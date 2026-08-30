import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Admin
from ..schemas import SetupRequest, SetupResponse, StatusResponse

router = APIRouter(tags=["setup"])


@router.get("/", response_model=StatusResponse)
def check_initialization(db: Session = Depends(get_db)):
    """
    Check whether an admin account exists.
    Returns initialized=False when the admin table is empty,
    signalling the frontend to show the first-run setup form.
    """
    admin_exists = db.query(Admin).first() is not None
    if admin_exists:
        return StatusResponse(initialized=True, message="System is ready.")
    return StatusResponse(
        initialized=False,
        message="No admin account found. Please complete the initial setup.",
    )


@router.post("/setup", response_model=SetupResponse)
def setup_admin(payload: SetupRequest, db: Session = Depends(get_db)):
    """
    Create the first admin account.
    Only works when no admin exists yet (first-run guard).
    """
    if db.query(Admin).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Setup already completed. An admin account already exists.",
        )

    hashed = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    admin = Admin(username=payload.username.strip(), password_hash=hashed)
    db.add(admin)
    db.commit()

    return SetupResponse(success=True, message="Admin account created successfully.")
