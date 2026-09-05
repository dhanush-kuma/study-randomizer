"""
core/investigators.py
Helper utilities for investigator username/password generation.
"""
import secrets

from sqlalchemy.orm import Session

from ..models import Investigator


def generate_username(study_id: int, db: Session) -> str:
    """
    Return the next zero-padded sequential username for the given study.
    Example: first investigator in any study → "000001", second → "000002", etc.
    Usernames are unique within a study but the same number can exist across studies.
    """
    result = (
        db.query(Investigator.username)
        .filter(Investigator.study_id == study_id)
        .all()
    )
    if not result:
        next_number = 1
    else:
        # Usernames are stored as zero-padded strings; convert to int for comparison
        max_number = max(int(row.username) for row in result)
        next_number = max_number + 1

    return f"{next_number:06d}"


def generate_temp_password() -> str:
    """
    Generate a random temporary password (URL-safe base64, ~16 printable chars).
    Long enough to be secure, short enough to type from an email.
    """
    return secrets.token_urlsafe(12)  # → 16-char URL-safe string
