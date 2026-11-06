"""Hunts assigned to the classes the signed-in student is enrolled in."""

import psycopg
from fastapi import APIRouter, Depends

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student/hunts", tags=["student"])


@router.get("", summary="List hunts assigned to your classes")
def assigned_hunts(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            return connection.execute(
                """SELECT assigned_hunts.id, classes.id AS class_id, classes.name AS class_name,
                    assigned_hunts.language_code, assigned_hunts.difficulty, assigned_hunts.due_date
                FROM assigned_hunts
                JOIN classes ON classes.id = assigned_hunts.class_id
                JOIN class_enrollments ON class_enrollments.class_id = classes.id
                WHERE class_enrollments.student_id = %s
                ORDER BY assigned_hunts.due_date NULLS LAST, assigned_hunts.assigned_at, assigned_hunts.id""",
                (user["id"],),
            ).fetchall()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
