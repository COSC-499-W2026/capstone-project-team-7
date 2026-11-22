"""The signed-in student's "My progress" details: finished games, totals and hardest locations."""

import psycopg
from fastapi import APIRouter, Depends

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student/progress", tags=["student"])


@router.get("/details", summary="Your finished games, totals, fastest and slowest game, and hardest locations")
def progress_details(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            games = connection.execute(
                """SELECT finished_at, language_code, difficulty, points,
                    FLOOR(EXTRACT(EPOCH FROM finished_at - started_at))::int AS time_seconds
                FROM game_sessions WHERE student_id = %s AND finished_at IS NOT NULL
                ORDER BY finished_at DESC, id""",
                (user["id"],),
            ).fetchall()
            # Only finished games, so a room number is never shown for a spot the student hasn't found yet.
            hardest_locations = connection.execute(
                """SELECT locations.building, locations.room_number, game_sessions.language_code,
                    game_sessions.difficulty, SUM(game_session_locations.listens)::int AS listens
                FROM game_session_locations
                JOIN game_sessions ON game_sessions.id = game_session_locations.game_session_id
                JOIN locations ON locations.id = game_session_locations.location_id
                WHERE game_sessions.student_id = %s AND game_sessions.finished_at IS NOT NULL
                GROUP BY locations.id, game_sessions.language_code, game_sessions.difficulty
                HAVING SUM(game_session_locations.listens) > 0
                ORDER BY SUM(game_session_locations.listens) DESC, SUM(game_session_locations.attempts) DESC,
                    locations.building, locations.room_number
                LIMIT 3""",
                (user["id"],),
            ).fetchall()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None

    per_language = {}
    for game in games:
        language = per_language.setdefault(game["language_code"],
                                           {"language_code": game["language_code"], "games_finished": 0, "points": 0})
        language["games_finished"] += 1
        language["points"] += game["points"]
    by_time = sorted(games, key=lambda game: game["time_seconds"])
    return {
        "total_points": sum(game["points"] for game in games),
        "games_finished": len(games),
        "games": games,
        "fastest_game": by_time[0] if games else None,
        "slowest_game": by_time[-1] if games else None,
        "hardest_locations": hardest_locations,
        "per_language": list(per_language.values()),
    }
