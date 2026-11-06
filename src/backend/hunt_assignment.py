"""Teachers assign a hunt to a class they own."""

from datetime import date
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, field_validator

from database import get_connection
from difficulties import Difficulty
from teacher_access import database_unavailable, owned_class, require_teacher, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])


class HuntAssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    difficulty: Difficulty
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def not_in_past(cls, value):
        if value is not None and value < date.today():
            raise ValueError("Due date cannot be in the past")
        return value


@router.post("/{class_id}/hunts", status_code=201, summary="Assign a hunt to a class; it uses the class's language")
def assign_hunt(class_id: UUID, info: HuntAssignmentRequest, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            classroom = connection.execute(
                "SELECT teacher_id, language_code FROM classes WHERE id = %s", (class_id,),
            ).fetchone()
            if not classroom:
                raise HTTPException(status_code=404, detail="Class not found")
            if classroom["teacher_id"] != user["id"]:
                raise HTTPException(status_code=403, detail="You can only assign hunts to your own classes")
            return connection.execute(
                """INSERT INTO assigned_hunts (class_id, language_code, difficulty, due_date)
                VALUES (%s, %s, %s, %s)
                RETURNING id, class_id, language_code, difficulty, due_date""",
                (class_id, classroom["language_code"], info.difficulty.value, info.due_date),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None


@router.get("/{class_id}/hunts", summary="List the hunts assigned to a class you own, newest first")
def list_hunts(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    if not owned_class(connection, class_id, teacher_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return connection.execute(
        """SELECT id, difficulty, due_date, assigned_at FROM assigned_hunts
        WHERE class_id = %s ORDER BY assigned_at DESC, id""", (class_id,),
    ).fetchall()


@router.delete("/{class_id}/hunts/{hunt_id}", status_code=204, summary="Delete a hunt from a class you own")
def delete_hunt(class_id: UUID, hunt_id: UUID, user=Depends(require_teacher)):
    try:
        with get_connection() as connection:
            if not owned_class(connection, class_id, user["id"]):
                raise HTTPException(status_code=404, detail="Class not found")
            deleted = connection.execute(
                "DELETE FROM assigned_hunts WHERE id = %s AND class_id = %s", (hunt_id, class_id),
            ).rowcount
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if not deleted:
        raise HTTPException(status_code=404, detail="Hunt not found")
    return Response(status_code=204)
