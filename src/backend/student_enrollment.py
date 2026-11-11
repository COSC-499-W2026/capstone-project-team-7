"""Students join a class by entering its class code."""

from typing import Annotated

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from auth import current_user
from database import get_connection
from schemas import RequiredText
from teacher_access import database_unavailable
from utils.enrollment import enroll

router = APIRouter(prefix="/api/student/classes", tags=["student"])


class JoinClassRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    class_code: Annotated[
        RequiredText,
        Field(max_length=12, description="Code the teacher shared, e.g. 'ABC123DEF456'"),
        AfterValidator(str.upper),
    ]


def require_student(user=Depends(current_user)):
    if user["role"] != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return user


@router.post("/join", status_code=201, summary="Enrol the signed-in student in a class by its code")
def join_class(info: JoinClassRequest, user=Depends(require_student)):
    try:
        with get_connection() as connection:
            classroom = connection.execute(
                "SELECT id, name, language_code FROM classes WHERE class_code = %s",
                (info.class_code,),
            ).fetchone()
            if not classroom:
                raise HTTPException(status_code=404, detail="Class not found")
            if not enroll(connection, classroom["id"], user["id"]):
                raise HTTPException(status_code=409, detail="Already enrolled")
            return classroom
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
