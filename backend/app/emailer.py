import aiosmtplib
from email.message import EmailMessage
from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, APP_ORIGIN

async def send_verification_email(to_email: str, token: str):
    if not SMTP_HOST:
        return
    link = f"{APP_ORIGIN}/verify?token={token}"
    msg = EmailMessage()
    msg["From"] = SMTP_FROM or SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = "Verify your PyChatX email"
    msg.set_content(f"Click to verify your account: {link}")
    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASS,
    )
