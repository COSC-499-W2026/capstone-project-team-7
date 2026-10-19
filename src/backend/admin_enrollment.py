"""Admin: enroll a registered student in any class."""

from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from admin import database_unavailable, require_admin
from database import get_connection
from schemas import RequiredText

router = APIRouter(prefix="/api/admin/classes", tags=["admin"])


class AdminEnrollment(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"student_number": "12345678"}]})
    student_number: Annotated[RequiredText, Field(max_length=30)]


@router.post("/{class_id}/students", status_code=201, dependencies=[Depends(require_admin)],
             summary="Enroll a registered student in a class by student number")
def enroll_student(class_id: UUID, info: AdminEnrollment):
    try:
        with get_connection() as connection:
            if not connection.execute("SELECT id FROM classes WHERE id = %s", (class_id,)).fetchone():
                raise HTTPException(status_code=404, detail="Class not found")
            student = connection.execute(
                "SELECT user_id, student_number FROM students WHERE student_number = %s",
                (info.student_number,),
            ).fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Student not found")
            connection.execute(
                "INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)",
                (class_id, student["user_id"]),
            )
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Student already enrolled") from None
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return {"class_id": class_id, "student_id": student["user_id"], "student_number": student["student_number"]}
