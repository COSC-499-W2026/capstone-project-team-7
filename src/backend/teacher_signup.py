"""Teacher registration backed by the administrator-managed email allowlist."""

import logging
from typing import Annotated

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database import get_connection
from utils.passwords import hash_password

router = APIRouter()
Text = Annotated[str, Field(min_length=1)]


class TeacherSignup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")]
    username: Annotated[str, Field(min_length=1, max_length=50)]
    password: Annotated[str, Field(min_length=8)]
    first_name: Text
    last_name: Text

    @field_validator("email", "username", "first_name", "last_name", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()

    @field_validator("password")
    @classmethod
    def check_password_bytes(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 UTF-8 bytes")
        return value


@router.post("/api/auth/teacher/signup", status_code=201)
def signup_teacher(info: TeacherSignup):
    try:
        with get_connection() as connection:
            authorized = connection.execute(
                "SELECT email FROM authorized_teacher_emails WHERE email = %s FOR SHARE",
                (info.email,),
            ).fetchone()
            if not authorized:
                raise HTTPException(status_code=403, detail="Error, unauthorized account")
            user = connection.execute(
                """INSERT INTO users (email, username, password, first_name, last_name, role)
                VALUES (%s, %s, %s, %s, %s, 'teacher') RETURNING id, role""",
                (info.email, info.username, hash_password(info.password),
                 info.first_name, info.last_name),
            ).fetchone()
            connection.execute("INSERT INTO teachers (user_id) VALUES (%s)", (user["id"],))
        return {"id": str(user["id"]), "role": user["role"]}
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Email or username already in use") from None
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Teacher signup database operation failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
