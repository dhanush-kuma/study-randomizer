import logging
import smtplib
from email.message import EmailMessage

from ..config import (
    FRONTEND_URL,
    IS_PRODUCTION,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
    email_is_configured,
)

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    if not email_is_configured():
        logger.warning(
            "Email not configured — would send to %s | subject: %s | body: %s",
            to,
            subject,
            body,
        )
        if IS_PRODUCTION:
            raise RuntimeError("Email service is not configured.")
        return

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        if SMTP_USE_TLS:
            server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)


def send_investigator_credentials(
    to_email: str,
    name: str | None,
    study_title: str,
    protocol_code: str,
    username: str,
    temp_password: str,
) -> None:
    login_url = f"{FRONTEND_URL.rstrip('/')}/investigator/login"
    greeting = name.strip() if name and name.strip() else "Investigator"

    subject = f"Your investigator credentials for study: {protocol_code}"
    body = f"""Hello {greeting},

You have been added as an investigator on a clinical study on Study Randomizer.

Study: {study_title}
Protocol code: {protocol_code}

Your login credentials:
  Username : {username}
  Password : {temp_password}

Login at: {login_url}

Use your Trial ID ({protocol_code}), username, and the password above to sign in.
You can change your password after logging in.

If you did not expect this email, please contact the study organizer.

— Study Randomizer
"""

    send_email(to_email, subject, body)
