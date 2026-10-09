"""Administrator-managed teacher signup approvals."""

import logging
from hashlib import sha256

import psycopg
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from auth import SESSION_COOKIE
from database import get_connection

router = APIRouter(prefix="/api/admin/approved-teachers", tags=["admin"])


class TeacherApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


@router.post("", status_code=201)
def approve_teacher(info: TeacherApproval, request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        with get_connection() as connection:
            user = connection.execute(
                """SELECT u.role FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s AND s.expires_at > now()""",
                (sha256(token.encode()).hexdigest(),),
            ).fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            if user["role"] != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            connection.execute(
                "INSERT INTO authorized_teacher_emails (email) VALUES (%s)", (info.email,),
            )
        return {"email": info.email, "approved": True}
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Teacher email already approved") from None
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Teacher approval database operation failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
