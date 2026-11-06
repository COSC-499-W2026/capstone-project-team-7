"""Issue expiring password-reset links without revealing registered emails."""

import logging
import secrets

import psycopg
from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from auth import SESSION_COOKIE, hash_token
from database import get_connection
from utils.mail import send_reset_email
from utils.passwords import hash_password, validate_password

router = APIRouter(prefix="/api/auth")


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    email: EmailStr


def issue_reset_token(email: str, token: str):
    with get_connection() as connection:
        return connection.execute(
            """WITH allowed AS (
                INSERT INTO password_reset_email_limits (user_id, requested_at)
                SELECT id, ARRAY[now()] FROM users WHERE lower(email) = lower(%s)
                ON CONFLICT (user_id) DO UPDATE SET requested_at =
                    ARRAY(SELECT sent_at FROM unnest(password_reset_email_limits.requested_at) AS sent_at
                          WHERE sent_at > now() - interval '1 hour') || ARRAY[now()]
                WHERE password_reset_email_limits.requested_at[cardinality(password_reset_email_limits.requested_at)]
                    < now() - interval '1 minute'
                AND (SELECT count(*) FROM unnest(password_reset_email_limits.requested_at) AS sent_at
                     WHERE sent_at > now() - interval '1 hour') < 5
                RETURNING user_id
            )
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            SELECT user_id, %s, now() + interval '30 minutes' FROM allowed
            ON CONFLICT (user_id) DO UPDATE SET token_hash = EXCLUDED.token_hash,
                created_at = now(), expires_at = EXCLUDED.expires_at
            RETURNING (SELECT email FROM users WHERE id = password_reset_tokens.user_id) AS email""",
            (email, hash_token(token)),
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


class PasswordResetSubmission(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    token: str = Field(min_length=1, max_length=256, repr=False)
    new_password: str = Field(min_length=8, repr=False)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return validate_password(value)


def complete_password_reset(token: str, password_hash: str):
    with get_connection() as connection:
        # Serialize password changes with login so old credentials cannot create a surviving session.
        user = connection.execute(
            """SELECT users.id FROM users JOIN password_reset_tokens ON users.id = user_id
               WHERE token_hash = %s AND expires_at > now() FOR NO KEY UPDATE OF users""",
            (hash_token(token),),
        ).fetchone()
        consumed = user and connection.execute(
            "DELETE FROM password_reset_tokens WHERE token_hash = %s AND expires_at > now() RETURNING user_id",
            (hash_token(token),),
        ).fetchone()
        if not consumed:
            raise HTTPException(status_code=422, detail="Reset link is invalid or expired. Request a new link.")
        connection.execute("UPDATE users SET password = %s WHERE id = %s", (password_hash, user["id"]))
        connection.execute("DELETE FROM sessions WHERE user_id = %s", (user["id"],))


@router.post("/reset-password", summary="Set a new password using an emailed reset token")
def reset_password(info: PasswordResetSubmission, response: Response):
    password_hash = hash_password(info.new_password)
    try:
        complete_password_reset(info.token, password_hash)
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Password reset failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=True, samesite="lax")
    return {"message": "Password reset successfully. Please log in with your new password."}
