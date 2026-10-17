"""Issue expiring password-reset links without revealing registered emails."""

import logging
import secrets

import psycopg
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr

from auth import hash_token
from database import get_connection
from utils.mail import send_reset_email

router = APIRouter(prefix="/api/auth")


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    email: EmailStr


def issue_reset_token(email: str, token: str):
    with get_connection() as connection:
        return connection.execute(
            """INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            SELECT id, %s, now() + interval '30 minutes' FROM users WHERE lower(email) = lower(%s)
            ON CONFLICT (user_id) DO UPDATE SET token_hash = EXCLUDED.token_hash,
                created_at = now(), expires_at = EXCLUDED.expires_at
            WHERE password_reset_tokens.created_at < now() - interval '1 minute'
            RETURNING (SELECT email FROM users WHERE id = password_reset_tokens.user_id) AS email""",
            (hash_token(token), email),
        ).fetchone()


@router.post("/forgot-password", summary="Request a password-reset email")
def forgot_password(info: PasswordResetRequest, background_tasks: BackgroundTasks):
    token = secrets.token_urlsafe(32)
    try:
        recipient = issue_reset_token(str(info.email), token)
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Password reset failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    if recipient:
        background_tasks.add_task(send_reset_email, recipient["email"], token)
    return {"message": "If an account matches that email, we'll send a reset link."}
