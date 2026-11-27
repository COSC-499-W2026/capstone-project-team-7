"""Per-student report for a class owned by the signed-in teacher."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from difficulties import Difficulty
from teacher_access import owned_class, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])
NO_GAMES = "No games completed yet"


def student_report_rows(connection, class_id, language_code):
    """One row per enrolled student. Counts the same games as the class leaderboard:
    finished (so never quit) and in the class's language."""
    students = connection.execute(
        """WITH spots AS (
            SELECT game_session_id, count(found_at) AS found,
                   SUM(cardinality(skipped_location_ids)) AS skipped
            FROM game_session_locations GROUP BY game_session_id
        )
        SELECT u.id AS student_id, u.first_name, u.last_name, u.username,
            COALESCE(SUM(g.points), 0)::int AS total_points,
            array_remove(array_agg(DISTINCT g.difficulty), NULL) AS difficulties_completed,
            COUNT(g.id)::int AS games_finished,
            COALESCE(EXTRACT(EPOCH FROM SUM(g.finished_at - g.started_at)), 0)::int AS total_game_seconds,
            EXTRACT(EPOCH FROM MIN(g.finished_at - g.started_at))::int AS fastest_game_seconds,
            COALESCE(SUM(spots.found), 0)::int AS locations_completed,
            COALESCE(SUM(spots.skipped), 0)::int AS locations_skipped
        FROM class_enrollments e
        JOIN users u ON u.id = e.student_id
        LEFT JOIN game_sessions g ON g.student_id = e.student_id
            AND g.language_code = %s AND g.finished_at IS NOT NULL
        LEFT JOIN spots ON spots.game_session_id = g.id
        WHERE e.class_id = %s AND e.status = 'enrolled'
        GROUP BY u.id
        ORDER BY lower(u.last_name), lower(u.first_name), u.username""",
        (language_code, class_id),
    ).fetchall()
    plays = connection.execute(
        """WITH clues AS (
            SELECT game_session_id, location_id, listens FROM game_session_locations
            UNION ALL
            -- Skips from before migration 019 have no saved count, so they show 0 plays.
            SELECT gl.game_session_id, skipped.location_id, COALESCE(skipped.listens, 0)
            FROM game_session_locations gl,
                unnest(gl.skipped_location_ids, gl.skipped_location_listens) AS skipped(location_id, listens)
        )
        SELECT g.student_id, l.id AS location_id, l.building, l.room_number,
            SUM(clues.listens)::int AS plays
        FROM class_enrollments e
        JOIN game_sessions g ON g.student_id = e.student_id
            AND g.language_code = %s AND g.finished_at IS NOT NULL
        JOIN clues ON clues.game_session_id = g.id
        JOIN locations l ON l.id = clues.location_id
        WHERE e.class_id = %s AND e.status = 'enrolled'
        GROUP BY g.student_id, l.id
        ORDER BY l.building, l.room_number""",
        (language_code, class_id),
    ).fetchall()
    report = {}
    for row in students:
        done = row["difficulties_completed"]
        report[row["student_id"]] = {**row, "clue_plays": [],
                                     "difficulties_completed": [d.value for d in Difficulty if d.value in done]}
        if row["fastest_game_seconds"] is None:
            report[row["student_id"]]["fastest_game_seconds"] = NO_GAMES
    for play in plays:
        report[play.pop("student_id")]["clue_plays"].append(play)
    return list(report.values())


@router.get("/{class_id}/report", summary="Read a per-student progress report for a class you teach")
def class_report(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    classroom = owned_class(connection, class_id, teacher_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return student_report_rows(connection, class_id, classroom["language_code"])
