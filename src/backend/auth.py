"""Login, logout and the current user: start, end and read cookie sessions."""

import logging
import secrets
from datetime import timedelta
from hashlib import sha256

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request, Response
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


def hash_token(token):
    return sha256(token.encode()).hexdigest()


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
                (hash_token(token), user["id"], SESSION_LIFETIME),
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


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    try:
        with get_connection() as connection:
            # Deleting the row invalidates the token; a missing or expired session is unauthorized.
            session = token and connection.execute(
                "DELETE FROM sessions WHERE token_hash = %s AND expires_at > now() RETURNING user_id",
                (hash_token(token),),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Logout failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")

    response.delete_cookie(SESSION_COOKIE, httponly=True, secure=True, samesite="lax")
    return {"status": "logged out"}


def current_user(request: Request):
    """Dependency for protected routes: the logged-in user, or 401 "Unauthorized"."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        with get_connection() as connection:
            user = connection.execute(
                """
                SELECT users.id, users.email, users.first_name, users.role
                FROM sessions JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = %s AND sessions.expires_at > now()
                """,
                (hash_token(token),),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Session check failed: database unavailable")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@router.get("/me", summary="The logged-in user and their dashboard")
def me(user=Depends(current_user)):
    return {
        "email": user["email"],
        "first_name": user["first_name"],
        "role": user["role"],
        "redirect_to": DASHBOARDS[user["role"]],
    }
