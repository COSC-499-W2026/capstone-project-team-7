"""Read and update the signed-in student's profile."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator

from database import get_connection
from schemas import RequiredText, Username
from student_enrollment import require_student

router = APIRouter(prefix="/api/student/profile", tags=["student"])


@router.get("", summary="Read your student profile")
def profile(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            account = connection.execute(
                """SELECT username, students.student_number, equipped_icon_id FROM users
                JOIN students ON students.user_id = users.id WHERE users.id = %s""",
                (user["id"],),
            ).fetchone()
            if account is None:
                raise HTTPException(status_code=404, detail="Student profile not found")
            classes = connection.execute(
                """SELECT classes.id, classes.name, classes.language_code
                FROM classes JOIN class_enrollments ON class_enrollments.class_id = classes.id
                WHERE class_enrollments.student_id = %s AND class_enrollments.status = 'enrolled'
                ORDER BY classes.name, classes.id""",
                (user["id"],),
            ).fetchall()
            languages = connection.execute(
                """SELECT code, name FROM languages WHERE code IN (
                    SELECT language_code FROM student_languages WHERE student_id = %s
                    UNION
                    SELECT classes.language_code FROM classes
                    JOIN class_enrollments ON class_enrollments.class_id = classes.id
                    WHERE class_enrollments.student_id = %s AND class_enrollments.status = 'enrolled'
                ) ORDER BY name""",
                (user["id"], user["id"]),
            ).fetchall()
            return {"username": account["username"], "student_number": account["student_number"], "classes": classes,
                    "languages": languages, "profile_icon": account["equipped_icon_id"]}
    except (psycopg.Error, RuntimeError):
        raise HTTPException(status_code=503, detail="Database unavailable") from None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: RequiredText | None = None
    last_name: RequiredText | None = None
    username: Username | None = None

    @model_validator(mode="after")
    def validate_changes(self):
        if not self.model_fields_set or any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Provide at least one name or username and omit fields you want to keep")
        return self


@router.patch("", summary="Update your name or username")
def update_profile(info: ProfileUpdate, user=Depends(require_student)):
    try:
        with get_connection() as connection:
            account = connection.execute(
                """UPDATE users
                SET first_name = COALESCE(%s, users.first_name),
                    last_name = COALESCE(%s, users.last_name),
                    username = COALESCE(%s, users.username)
                FROM students WHERE students.user_id = users.id AND users.id = %s AND users.role = 'student'
                RETURNING users.first_name, users.last_name, users.username""",
                (info.first_name, info.last_name, info.username, user["id"]),
            ).fetchone()
            if account is None:
                raise HTTPException(status_code=404, detail="Student profile not found")
    except (psycopg.Error, RuntimeError) as error:
        if isinstance(error, psycopg.errors.UniqueViolation) and error.diag.constraint_name == "users_username_unique":
            raise HTTPException(status_code=409, detail="Username already in use") from None
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return account
