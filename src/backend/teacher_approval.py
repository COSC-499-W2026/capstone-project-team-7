"""Administrator-managed teacher signup approvals."""

import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from admin import require_admin
from database import get_connection

router = APIRouter(prefix="/api/admin/approved-teachers", tags=["admin"])


class TeacherApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


@router.post("", status_code=201, summary="Approve an email for teacher signup",
             dependencies=[Depends(require_admin)])
def approve_teacher(info: TeacherApproval):
    try:
        with get_connection() as connection:
            connection.execute(
                "INSERT INTO authorized_teacher_emails (email) VALUES (%s)", (info.email,),
            )
        return {"email": info.email, "approved": True}
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Teacher email already approved") from None
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Teacher approval database operation failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
