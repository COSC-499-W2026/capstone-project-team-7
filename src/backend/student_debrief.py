"""Summarize signs of difficulty across a student's completed hunts."""

import psycopg
from fastapi import APIRouter, Depends

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable
from utils.completed_locations import completed_location_activity, debrief_locations

router = APIRouter(prefix="/api/student/debrief", tags=["student"])


@router.get("", summary="Summarize difficulties in your completed hunts")
def get_debrief(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            completed = connection.execute(
                """SELECT count(*)::int AS completed_hunts FROM game_sessions
                WHERE student_id = %s AND finished_at IS NOT NULL AND quit_at IS NULL""",
                (user["id"],),
            ).fetchone()["completed_hunts"]
            activity = completed_location_activity(connection, user["id"])
            difficulties = debrief_locations(activity)
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return {"completed_hunts": completed, "difficulties": difficulties}
