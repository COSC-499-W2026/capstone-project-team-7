"""The signed-in student's badges, earned and locked."""

import psycopg
from fastapi import APIRouter, Depends

from badges import list_badges
from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student/badges", tags=["student"])


@router.get("", summary="List every badge, marking the ones you have earned")
def badges(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            return list_badges(connection, user["id"])
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
