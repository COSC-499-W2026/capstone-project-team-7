"""Classes owned by the signed-in teacher: create, list, and read."""

import logging
from hashlib import sha256
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from auth import SESSION_COOKIE, current_user
from database import get_connection
from schemas import RequiredText

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


class ClassCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: RequiredText
    language_code: Annotated[RequiredText, Field(max_length=5, description="Language code, e.g. 'fr'")]


def database_unavailable():
    logging.getLogger(__name__).warning("Teacher class access database operation failed")
    return HTTPException(status_code=503, detail="Database unavailable")


def teacher_connection(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Login required")
    try:
        with get_connection() as connection:
            user = connection.execute(
                """SELECT u.id, u.role FROM sessions s JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s AND s.expires_at > now()""",
                (sha256(token.encode()).hexdigest(),),
            ).fetchone()
            if not user:
                raise HTTPException(status_code=401, detail="Login required")
            if user["role"] != "teacher":
                raise HTTPException(status_code=403, detail="Teacher access required")
            yield connection, user["id"]
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


def require_teacher(user=Depends(current_user)):
    """Only let logged-in teachers through; current_user already rejects missing or expired sessions."""
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required")
    return user


@router.post("", status_code=201, summary="Create a class owned by the signed-in teacher")
def create_class(info: ClassCreate, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            return connection.execute(
                """INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, %s, %s)
                RETURNING id, name, language_code, class_code""",
                (user["id"], info.name, info.language_code),
            ).fetchone()
    except psycopg.errors.ForeignKeyViolation as error:
        if error.diag.constraint_name != "classes_language_code_fkey":
            raise database_unavailable() from None
        raise HTTPException(status_code=422, detail="Unknown language") from None
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


@router.get("")
def list_classes(access=Depends(teacher_connection)):
    connection, teacher_id = access
    return connection.execute(
        """SELECT id, name, language_code, class_code FROM classes
        WHERE teacher_id = %s ORDER BY name, id""", (teacher_id,),
    ).fetchall()


@router.get("/{class_id}")
def get_class(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    classroom = connection.execute(
        """SELECT id, name, language_code, class_code FROM classes
        WHERE id = %s AND teacher_id = %s""", (class_id, teacher_id),
    ).fetchone()
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return classroom
