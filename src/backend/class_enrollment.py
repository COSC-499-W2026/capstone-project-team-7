"""Enroll registered students in a class owned by the signed-in teacher."""

from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from schemas import RequiredText
from teacher_access import database_unavailable, owned_class, require_teacher

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


class EnrollmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_number: Annotated[RequiredText, Field(max_length=30)]


@router.post("/{class_id}/students", status_code=201, summary="Enroll a registered student by student number")
def enroll_student(class_id: UUID, info: EnrollmentRequest, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            if not owned_class(connection, class_id, user["id"]):
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
