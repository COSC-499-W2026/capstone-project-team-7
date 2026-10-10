"""Admin: reassign a class to a different approved teacher."""

import logging
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import current_user
from database import get_connection

router = APIRouter(prefix="/api/admin")


def database_unavailable():
    logging.getLogger(__name__).warning("Admin request failed: database unavailable")
    return HTTPException(status_code=503, detail="Database unavailable")


def require_admin(user=Depends(current_user)):
    """Only let logged-in admins through; current_user already rejects missing or expired sessions."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")


class TeacherAssignment(BaseModel):
    teacher_email: str


@router.patch("/classes/{class_id}/teacher", dependencies=[Depends(require_admin)])
def reassign_class(class_id: UUID, assignment: TeacherAssignment):
    try:
        with get_connection() as connection:
            # The teacher must have a teacher account and be on the approved list.
            teacher = connection.execute(
                """SELECT teachers.user_id FROM teachers
                JOIN users ON users.id = teachers.user_id
                JOIN authorized_teacher_emails approved ON approved.email = lower(users.email)
                WHERE lower(users.email) = lower(%s)""",
                (assignment.teacher_email.strip(),),
            ).fetchone()
            if teacher is None:
                raise HTTPException(status_code=400, detail="Invalid teacher")
            # Only the teacher changes; enrollments and progress reference the class, not the teacher.
            course = connection.execute(
                "UPDATE classes SET teacher_id = %s WHERE id = %s RETURNING id, teacher_id",
                (teacher["user_id"], class_id),
            ).fetchone()
            if course is None:
                raise HTTPException(status_code=404, detail="Class not found")
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return course
