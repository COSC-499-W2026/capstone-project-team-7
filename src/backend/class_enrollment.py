"""Enroll and remove students in a class owned by the signed-in teacher."""

from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from schemas import RequiredText
from teacher_access import database_unavailable, owned_class, require_teacher
from utils.enrollment import enroll

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
            if not enroll(connection, class_id, student["user_id"]):
                raise HTTPException(status_code=409, detail="Student already enrolled")
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return {"class_id": class_id, "student_id": student["user_id"], "student_number": student["student_number"]}


@router.delete("/{class_id}/students/{student_id}", status_code=204,
               summary="Remove a student from a class; their account and class history are kept")
def remove_student(class_id: UUID, student_id: UUID, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            if not owned_class(connection, class_id, user["id"]):
                raise HTTPException(status_code=404, detail="Class not found")
            removed = connection.execute(
                """UPDATE class_enrollments SET status = 'unenrolled', unenrolled_at = now()
                WHERE class_id = %s AND student_id = %s AND status = 'enrolled'""",
                (class_id, student_id),
            ).rowcount
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if not removed:
        raise HTTPException(status_code=404, detail="Student not enrolled")
    return Response(status_code=204)
