"""Persist validated student signup fields atomically."""

import psycopg

from database import get_connection
from utils.passwords import hash_password


class DuplicateStudentAccount(ValueError):
    """A signup identity is already registered."""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"{field.replace('_', ' ').capitalize()} already in use")


def create_student(*, email: str, password: str, first_name: str, last_name: str,
                   student_number: str, username: str) -> dict:
    """Accept validated fields; commit both rows or neither, returning no credentials."""
    password_hash = hash_password(password)
    student_number = student_number.strip()
    try:
        with get_connection() as connection:
            user = connection.execute(
                """INSERT INTO users (email, password, first_name, last_name, username, role)
                   VALUES (%s, %s, %s, %s, %s, 'student')
                   RETURNING id, email, first_name, last_name, username, role""",
                (email.strip().lower(), password_hash, first_name.strip(),
                 last_name.strip(), username.strip()),
            ).fetchone()
            connection.execute(
                "INSERT INTO students (user_id, student_number) VALUES (%s, %s)",
                (user["id"], student_number),
            )
    except psycopg.errors.UniqueViolation as error:
        field = {
            "users_email_unique": "email",
            "users_username_unique": "username",
            "students_student_number_key": "student_number",
        }.get(error.diag.constraint_name)
        if field is None:
            raise
        raise DuplicateStudentAccount(field) from None
    return {**user, "student_number": student_number}
