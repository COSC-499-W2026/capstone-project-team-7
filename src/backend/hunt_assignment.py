"""Teachers assign a hunt to a class they own."""

from datetime import date
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator

from database import get_connection
from difficulties import Difficulty
from teacher_access import database_unavailable, require_teacher

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
