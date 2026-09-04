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


def send_study_invitation(
    to_email: str,
    doctor_name: str | None,
    study_title: str,
    protocol_code: str,
    invitation_token: str,
) -> None:
    signup_url = f"{FRONTEND_URL.rstrip('/')}/doctor/signup?token={invitation_token}"
    greeting = doctor_name.strip() if doctor_name and doctor_name.strip() else "Doctor"

    subject = f"Invitation to join study: {protocol_code}"
    body = f"""Hello {greeting},

You have been invited to join a clinical study on Study Randomizer.

Study: {study_title}
Protocol code: {protocol_code}

Create your account using this link (expires in 7 days):
{signup_url}

If you already have a doctor account, log in and accept the invitation from the same link.

If you did not expect this email, you can ignore it.

— Study Randomizer
"""

    send_email(to_email, subject, body)
