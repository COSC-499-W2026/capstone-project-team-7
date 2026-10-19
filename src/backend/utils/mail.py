"""Send password-reset links through Gmail using an App Password."""

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage


def send_reset_email(recipient: str, token: str):
    try:
        username = os.environ["SMTP_USERNAME"]
        password = os.environ["SMTP_APP_PASSWORD"]
        message = EmailMessage()
        message["From"], message["To"] = username, recipient
        message["Subject"] = "Reset your Lost In Translation password"
        link = f"{os.environ['FRONTEND_URL'].rstrip('/')}/reset-password?token={token}"
        message.set_content(f"Reset your password: {link}\n\nThis link expires in 30 minutes. "
                            "If you did not request it, ignore this email.")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10,
                              context=ssl.create_default_context()) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, KeyError, ValueError):
        logging.getLogger(__name__).warning("Password reset email could not be sent")
