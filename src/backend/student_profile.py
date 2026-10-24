"""Read the signed-in student's own account details."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from student_enrollment import require_student

router = APIRouter(prefix="/api/student/profile", tags=["student"])


@router.get("", summary="Read your student profile")
@router.get("/{student_id}", summary="Read your own student profile by ID")
def profile(student_id: UUID | None = None, user=Depends(require_student)):
    if student_id is not None and student_id != UUID(str(user["id"])):
        raise HTTPException(status_code=403, detail="You can only access your own profile")
    try:
        with get_connection() as connection:
            account = connection.execute(
                "SELECT username FROM users JOIN students ON students.user_id = users.id WHERE users.id = %s",
                (user["id"],),
            ).fetchone()
            if account is None:
                raise HTTPException(status_code=404, detail="Student profile not found")
            classes = connection.execute(
                """SELECT classes.id, classes.name, classes.language_code
                FROM classes JOIN class_enrollments ON class_enrollments.class_id = classes.id
                WHERE class_enrollments.student_id = %s ORDER BY classes.name, classes.id""",
                (user["id"],),
            ).fetchall()
            languages = connection.execute(
                """SELECT code, name FROM languages WHERE code IN (
                    SELECT language_code FROM student_languages WHERE student_id = %s
                    UNION
                    SELECT classes.language_code FROM classes
                    JOIN class_enrollments ON class_enrollments.class_id = classes.id
                    WHERE class_enrollments.student_id = %s
                ) ORDER BY name""",
                (user["id"], user["id"]),
            ).fetchall()
            return {"username": account["username"], "classes": classes,
                    "languages": languages, "profile_icon": None}
    except (psycopg.Error, RuntimeError):
        raise HTTPException(status_code=503, detail="Database unavailable") from None
