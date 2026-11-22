"""Summarize signs of difficulty across a student's completed hunts."""

import psycopg
from fastapi import APIRouter, Depends

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable

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
            difficulties = connection.execute(
                """SELECT locations.building, locations.room_number, game_sessions.language_code,
                    game_sessions.difficulty, count(*)::int AS hunts,
                    sum(game_session_locations.listens)::int AS listens,
                    sum(game_session_locations.attempts)::int AS attempts,
                    sum(GREATEST(game_session_locations.attempts - 1, 0))::int AS extra_attempts
                FROM game_session_locations
                JOIN game_sessions ON game_sessions.id = game_session_locations.game_session_id
                JOIN locations ON locations.id = game_session_locations.location_id
                WHERE game_sessions.student_id = %s AND game_sessions.finished_at IS NOT NULL
                    AND game_sessions.quit_at IS NULL
                GROUP BY locations.id, game_sessions.language_code, game_sessions.difficulty
                HAVING bool_or(game_session_locations.listens > 1 OR game_session_locations.attempts > 1)
                ORDER BY sum(GREATEST(game_session_locations.attempts - 1, 0)) DESC,
                    sum(game_session_locations.listens) DESC, locations.building, locations.room_number,
                    game_sessions.language_code, game_sessions.difficulty
                LIMIT 3""",
                (user["id"],),
            ).fetchall()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    return {"completed_hunts": completed, "difficulties": difficulties}
