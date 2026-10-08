"""Login: check credentials and start a cookie session."""

import logging
import secrets
from datetime import timedelta
from hashlib import sha256

import psycopg
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from database import get_connection
from utils.passwords import verify_password

router = APIRouter(prefix="/api/auth")

SESSION_COOKIE = "session"
SESSION_LIFETIME = timedelta(days=7)
MAX_PASSWORD_BYTES = 72 # bcrypt only uses the first 72 bytes of a password.

# The frontend sends each role to its own dashboard after login.
DASHBOARDS = {
    "student": "/student/dashboard",
    "teacher": "/teacher/dashboard",
    "admin": "/admin/dashboard",
}


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(credentials: LoginRequest, response: Response):
    try:
        with get_connection() as connection:
            user = connection.execute(
                "SELECT id, password, role FROM users WHERE lower(email) = lower(%s)",
                (credentials.email.strip(),),
            ).fetchone()
            # Unknown email and wrong password get the same error so emails cannot be probed.
            if (
                user is None
                or len(credentials.password.encode("utf-8")) > MAX_PASSWORD_BYTES
                or not verify_password(credentials.password, user["password"])
            ):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            token = secrets.token_urlsafe(32)
            connection.execute(
                "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + %s)",
                (sha256(token.encode()).hexdigest(), user["id"], SESSION_LIFETIME),
            )
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Login failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None

    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"role": user["role"], "redirect_to": DASHBOARDS[user["role"]]}
