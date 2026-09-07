import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not email or not EMAIL_RE.match(email):
        raise ValueError("A valid email address is required.")
    return email
