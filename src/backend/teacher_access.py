"""Read access to classes assigned to the signed-in teacher."""

import logging
from hashlib import sha256
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request

from auth import SESSION_COOKIE
from database import get_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


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
        logging.getLogger(__name__).warning("Teacher class access database operation failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None


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
