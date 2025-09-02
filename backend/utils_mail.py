# backend/app/utils_mail.py
import ssl
import logging
from email.message import EmailMessage
import aiosmtplib

from .config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM,
    APP_ORIGIN, FRONTEND_BASE_URL, BACKEND_URL,
)

log = logging.getLogger("mail")


def _from_addr() -> str:
    # Prefer explicit SMTP_FROM, otherwise fall back to the SMTP user address with a nice name.
    return SMTP_FROM or (f"PyChatX <{SMTP_USER}>" if SMTP_USER else "PyChatX <noreply@localhost>")


def _fe_base() -> str:
    # Where the verify/join pages live (Vercel site). Fallback to APP_ORIGIN or localhost dev.
    return (FRONTEND_BASE_URL or APP_ORIGIN or "http://localhost:5173").rstrip("/")


def _be_base() -> str:
    # Render backend base; only used to include a backend fallback verify link in emails.
    return (BACKEND_URL or "").rstrip("/")


async def _send(msg: EmailMessage) -> bool:
    """Low-level SMTP sender with STARTTLS + login."""
    if not (SMTP_HOST and SMTP_PORT and SMTP_USER and SMTP_PASS):
        log.error("SMTP env vars missing; cannot send mail.")
        raise RuntimeError("SMTP not configured (SMTP_HOST/PORT/USER/PASS)")

    context = ssl.create_default_context()
    port = int(SMTP_PORT)

    # aiosmtplib handles async SMTP with STARTTLS
    async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=port) as smtp:
        await smtp.starttls(context=context)
        await smtp.login(SMTP_USER, SMTP_PASS)
        await smtp.send_message(msg)

    return True


async def send_verification_email(to_email: str, token: str) -> None:
    """
    Send an account verification email with BOTH:
      - Frontend link (preferred)  -> https://<vercel>/verify?token=...
      - Backend fallback link      -> https://<render>/auth/verify?token=...
    """
    fe = _fe_base()
    be = _be_base()

    verify_front = f"{fe}/verify?token={token}"
    verify_back = f"{be}/auth/verify?token={token}" if be else ""

    msg = EmailMessage()
    msg["Subject"] = "Verify your PyChatX account"
    msg["From"] = _from_addr()
    msg["To"] = to_email

    text = f"""Verify your PyChatX account

Click this link to verify:
{verify_front}

If that doesn’t work, try the backend fallback:
{verify_back or '-'}

If you already verified, you can ignore this email."""
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif">
      <h2>Verify your PyChatX account</h2>
      <p>Click the button below to verify your email.</p>
      <p>
        <a href="{verify_front}"
           style="background:#3b82f6;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;display:inline-block">
           Verify Email
        </a>
      </p>
      <p>If the button doesn’t work, copy this link and open it:</p>
      <p><code>{verify_front}</code></p>
      {f'<p>Backend fallback:<br><code>{verify_back}</code></p>' if verify_back else ''}
      <p>This link is single-use. If you’re already verified, this will just confirm it.</p>
    </div>
    """

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        await _send(msg)
        log.info("Verification email sent to %s", to_email)
    except Exception as e:
        log.exception("Failed to send verification email to %s: %s", to_email, e)
        raise


async def send_room_invite_email(to_email: str, room_name: str, invite_code: str) -> None:
    """
    Optional helper if you decide to email invite links.
    The frontend should have a page to consume ?code= and call /rooms/join.
    """
    fe = _fe_base()
    url = f"{fe}/invite?code={invite_code}"

    msg = EmailMessage()
    msg["Subject"] = f"You’re invited to “{room_name}” on PyChatX"
    msg["From"] = _from_addr()
    msg["To"] = to_email

    text = f"""You’ve been invited to the room: {room_name}

Join via this link:
{url}

If you’re not signed in, you’ll be asked to sign up / log in first.
"""
    html = f"""
    <div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif">
      <h2>Room invite: {room_name}</h2>
      <p>You’ve been invited to join this room on PyChatX.</p>
      <p>
        <a href="{url}"
           style="background:#10b981;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;display:inline-block">
           Join room
        </a>
      </p>
      <p>If that doesn’t work, copy this link:</p>
      <p><code>{url}</code></p>
    </div>
    """

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        await _send(msg)
        log.info("Invite email sent to %s", to_email)
    except Exception as e:
        log.exception("Failed to send invite email to %s: %s", to_email, e)
        raise
