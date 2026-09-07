import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage
from urllib.parse import quote

from ..config import (
    FRONTEND_URL,
    IS_PRODUCTION,
    RESEND_API_KEY,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
    email_is_configured,
)

logger = logging.getLogger(__name__)


def _send_via_resend(to: str, subject: str, body: str) -> None:
    """Send email using Resend's HTTP API (avoids outbound SMTP port blocks)."""
    payload = json.dumps({
        "from": SMTP_FROM,
        "to": [to],
        "subject": subject,
        "text": body,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "resend-python/2.0.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"Resend API returned status {resp.status}")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode(errors="replace")
        logger.error("Resend API error %s: %s", exc.code, body_text)
        raise RuntimeError(f"Resend API error {exc.code}: {body_text}") from exc


def _send_via_smtp(to: str, subject: str, body: str) -> None:
    """Send email via SMTP (port 465 = SSL, port 587 = STARTTLS)."""
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    use_ssl = SMTP_PORT == 465
    if use_ssl:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)


def send_email(to: str, subject: str, body: str) -> None:
    if not email_is_configured():
        logger.warning(
            "Email not configured — would send to %s | subject: %s "
            "(body omitted; may contain credentials)",
            to,
            subject,
        )
        if IS_PRODUCTION:
            raise RuntimeError("Email service is not configured.")
        return

    try:
        if RESEND_API_KEY:
            # Preferred on Railway — HTTP API bypasses SMTP port restrictions.
            _send_via_resend(to, subject, body)
        else:
            _send_via_smtp(to, subject, body)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        raise RuntimeError(f"Failed to send email: {exc}") from exc


def send_investigator_credentials(
    to_email: str,
    name: str | None,
    study_title: str,
    protocol_code: str,
    username: str,
    temp_password: str,
) -> None:
    trial_id = protocol_code.strip()
    login_url = (
        f"{FRONTEND_URL.rstrip('/')}/investigator/login?tid={quote(trial_id, safe='')}"
    )
    greeting = name.strip() if name and name.strip() else "Investigator"

    subject = f"Your investigator credentials for study: {study_title}"
    body = f"""Hello {greeting},

You have been added as an investigator on a clinical study on Study Randomizer.

Study: {study_title}

Your login credentials:
  Trial ID : {trial_id}
  Username : {username}
  Password : {temp_password}

Login at: {login_url}

Open the link above to sign in.
You can change your password after logging in.

If you did not expect this email, please contact the study organizer.

— Study Randomizer
"""

    send_email(to_email, subject, body)
