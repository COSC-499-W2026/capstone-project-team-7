"""Change a logged-in user's password and revoke their sessions."""

import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from auth import MAX_PASSWORD_BYTES, SESSION_COOKIE, current_user
from database import get_connection
from utils.passwords import hash_password, validate_password, verify_password

router = APIRouter(prefix="/api/auth")


class PasswordChangeRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    current_password: str = Field(repr=False)
    new_password: str = Field(min_length=8, repr=False)

    _validate_new_password = field_validator("new_password")(validate_password)


def replace_password(user_id, info: PasswordChangeRequest):
    with get_connection() as connection:
        user = connection.execute(
            "SELECT password FROM users WHERE id = %s FOR UPDATE", (user_id,),
        ).fetchone()
        if user is None:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if (len(info.current_password.encode("utf-8")) > MAX_PASSWORD_BYTES
                or not verify_password(info.current_password, user["password"])):
            raise HTTPException(status_code=403, detail="Current password is incorrect")
        connection.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hash_password(info.new_password), user_id),
        )
        connection.execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))


@router.post("/change-password", summary="Change your password and sign out of all sessions")
def change_password(info: PasswordChangeRequest, response: Response, user=Depends(current_user)):
    try:
        replace_password(user["id"], info)
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Password change failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=True, samesite="lax")
    return {"message": "Password changed. Please log in again."}
