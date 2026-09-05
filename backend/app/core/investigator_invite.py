"""
Shared logic for inviting investigators (single or bulk).
"""
import csv
import io
import re

import bcrypt
from sqlalchemy.orm import Session

from ..models import Investigator, Study
from .email import send_investigator_credentials
from .investigators import generate_temp_password, generate_username

MAX_BULK_ROWS = 100
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class DuplicateInvestigatorError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"An active investigator with email '{email}' already exists in this study.")


def parse_investigator_csv(content: bytes) -> list[tuple[int, str | None, str]]:
    """
    Parse a 2-column CSV (email, name) with no header row.
    Returns list of (row_number, name_or_none, email).
    """
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded.") from exc

    rows: list[tuple[int, str | None, str]] = []
    reader = csv.reader(io.StringIO(text))

    for line_num, row in enumerate(reader, start=1):
        if not row or all(not cell.strip() for cell in row):
            continue
        if len(row) != 2:
            raise ValueError(
                f"Row {line_num}: expected exactly 2 columns (email, name), found {len(row)}."
            )

        email_raw, name_raw = row[0].strip().lower(), row[1].strip()
        if not email_raw:
            raise ValueError(f"Row {line_num}: email is required.")
        if not _EMAIL_RE.match(email_raw):
            raise ValueError(f"Row {line_num}: invalid email address '{email_raw}'.")

        name = name_raw if name_raw else None
        rows.append((line_num, name, email_raw))

    if not rows:
        raise ValueError("CSV file contains no data rows.")

    if len(rows) > MAX_BULK_ROWS:
        raise ValueError(f"CSV may contain at most {MAX_BULK_ROWS} investigators per upload.")

    return rows


def active_investigator_exists(study_id: int, email: str, db: Session) -> bool:
    return (
        db.query(Investigator)
        .filter(
            Investigator.study_id == study_id,
            Investigator.email == email,
            Investigator.status != "revoked",
        )
        .first()
        is not None
    )


def create_and_send_investigator_invite(
    *,
    study: Study,
    email: str,
    name: str | None,
    db: Session,
) -> Investigator:
    """
    Create an investigator, send credential email, and flush to DB.
    Caller is responsible for commit/rollback.
    """
    if active_investigator_exists(study.id, email, db):
        raise DuplicateInvestigatorError(email)

    username = generate_username(study.id, db)
    temp_password = generate_temp_password()
    password_hash = bcrypt.hashpw(temp_password.encode(), bcrypt.gensalt()).decode()

    investigator = Investigator(
        study_id=study.id,
        email=email,
        name=name,
        username=username,
        password_hash=password_hash,
        status="inactive",
    )
    db.add(investigator)
    db.flush()

    send_investigator_credentials(
        to_email=investigator.email,
        name=investigator.name,
        study_title=study.title,
        protocol_code=study.protocol_code,
        username=username,
        temp_password=temp_password,
    )
    return investigator
