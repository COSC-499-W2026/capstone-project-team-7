"""The signed-in student's "My progress" details: finished games, totals and hardest locations."""

import psycopg
from fastapi import APIRouter, Depends

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable
from utils.completed_locations import completed_location_activity, progress_locations

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
            activity = completed_location_activity(connection, user["id"], include_quit=True)
            hardest_locations = progress_locations(activity)
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
