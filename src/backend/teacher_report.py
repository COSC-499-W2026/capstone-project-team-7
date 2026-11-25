"""Class report for the signed-in teacher: per-student rows, hardest levels, and a CSV download."""

import csv
import io
import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response

from difficulties import Difficulty
from teacher_access import owned_class, teacher_connection

router = APIRouter(prefix="/api/teacher/classes", tags=["teacher"])
NO_GAMES = "No games completed yet"
SCHOOL_TIME_ZONE = "America/Vancouver"  # UBCO is in Kelowna; the server clock runs in UTC.
HARDEST = {"most_skipped": "skips", "most_replayed": "plays", "most_attempts": "attempts"}

# The same games as the class leaderboard: finished (so never quit), in the class's language,
# by students still enrolled. Every report query starts from these.
CLASS_GAMES = """class_games AS (
    SELECT g.* FROM class_enrollments e
    JOIN game_sessions g ON g.student_id = e.student_id
        AND g.language_code = %(language)s AND g.finished_at IS NOT NULL
    WHERE e.class_id = %(class_id)s AND e.status = 'enrolled'
)"""
# Every clue a game showed: the one at each spot, plus the ones skipped there.
# Skips from before migrations 019 and 020 have no saved plays or attempts, so they show 0.
CLUES = """clues AS (
    SELECT game_session_id, location_id, listens, attempts, 0 AS skipped FROM game_session_locations
    UNION ALL
    SELECT gl.game_session_id, s.location_id, COALESCE(s.listens, 0), COALESCE(s.attempts, 0), 1
    FROM game_session_locations gl,
        unnest(gl.skipped_location_ids, gl.skipped_location_listens, gl.skipped_location_attempts)
            AS s(location_id, listens, attempts)
)"""


def student_report_rows(connection, class_id, language_code):
    """One row per enrolled student, built from the class's games."""
    params = {"language": language_code, "class_id": class_id}
    students = connection.execute(
        "WITH " + CLASS_GAMES + """, spots AS (
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
        LEFT JOIN class_games g ON g.student_id = e.student_id
        LEFT JOIN spots ON spots.game_session_id = g.id
        WHERE e.class_id = %(class_id)s AND e.status = 'enrolled'
        GROUP BY u.id
        ORDER BY lower(u.last_name), lower(u.first_name), u.username""",
        params,
    ).fetchall()
    plays = connection.execute(
        "WITH " + CLASS_GAMES + ", " + CLUES + """
        SELECT g.student_id, l.id AS location_id, l.building, l.room_number,
            SUM(clues.listens)::int AS plays
        FROM class_games g
        JOIN clues ON clues.game_session_id = g.id
        JOIN locations l ON l.id = clues.location_id
        GROUP BY g.student_id, l.id
        ORDER BY l.building, l.room_number""",
        params,
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


def hardest_levels(connection, class_id, language_code):
    """Levels (a location on one difficulty) ranked by skips, audio plays and photo attempts."""
    levels = connection.execute(
        "WITH " + CLASS_GAMES + ", " + CLUES + """
        SELECT l.building, l.room_number, g.difficulty,
            SUM(clues.skipped)::int AS skips, SUM(clues.listens)::int AS plays,
            SUM(clues.attempts)::int AS attempts
        FROM class_games g
        JOIN clues ON clues.game_session_id = g.id
        JOIN locations l ON l.id = clues.location_id
        GROUP BY l.id, g.difficulty
        ORDER BY l.building, l.room_number, array_position(ARRAY['basic', 'advanced', 'expert'], g.difficulty)""",
        {"language": language_code, "class_id": class_id},
    ).fetchall()
    ranked = {}
    for name, count in HARDEST.items():
        # sorted() keeps the building/room order for ties.
        top = sorted((level for level in levels if level[count] > 0), key=lambda level: -level[count])
        ranked[name] = [{"building": level["building"], "room_number": level["room_number"],
                         "difficulty": level["difficulty"], "count": level[count]} for level in top]
    return ranked


def readable_time(seconds):
    if not isinstance(seconds, int):
        return seconds
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s"


def safe_cell(value):
    # A leading =, +, - or @ makes Excel run the text as a formula.
    return "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value


def report_csv(students, levels):
    out = io.StringIO()
    writer = csv.writer(out)
    rows = [["Full name", "Username", "Total points", "Difficulties completed", "Games finished",
             "Total game time", "Fastest game time", "Locations completed", "Locations skipped", "Audio plays per clue"]]
    for s in students:
        plays = "; ".join(f"{p['building']} {p['room_number']}: {p['plays']}" for p in s["clue_plays"])
        rows.append([f"{s['first_name']} {s['last_name']}", s["username"], s["total_points"],
                     ", ".join(d.title() for d in s["difficulties_completed"]), s["games_finished"],
                     readable_time(s["total_game_seconds"]), readable_time(s["fastest_game_seconds"]),
                     s["locations_completed"], s["locations_skipped"], plays])
    for name, count in HARDEST.items():
        rows += [[], [name.replace("_", " ").capitalize() + " levels"],
                 ["Building", "Room", "Difficulty", count.capitalize()]]
        rows += [[l["building"], l["room_number"], l["difficulty"].title(), l["count"]] for l in levels[name]]
    writer.writerows([safe_cell(value) for value in row] for row in rows)
    return out.getvalue()


def owned_classroom(connection, class_id, teacher_id):
    classroom = owned_class(connection, class_id, teacher_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")
    return classroom


@router.get("/{class_id}/report", summary="Read a progress report for a class you teach")
def class_report(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    language = owned_classroom(connection, class_id, teacher_id)["language_code"]
    return {"students": student_report_rows(connection, class_id, language),
            "hardest_levels": hardest_levels(connection, class_id, language)}


@router.get("/{class_id}/report.csv", summary="Download the progress report for a class you teach as CSV")
def class_report_csv(class_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    classroom = owned_classroom(connection, class_id, teacher_id)
    language = classroom["language_code"]
    text = report_csv(student_report_rows(connection, class_id, language),
                      hardest_levels(connection, class_id, language))
    # Only letters, digits, _ and single dashes so the class name can't break the download header.
    name = re.sub(r"[^A-Za-z0-9_]+", "-", classroom["name"]).strip("-") or "class"
    today = connection.execute("SELECT (now() AT TIME ZONE %s)::date AS today", (SCHOOL_TIME_ZONE,)).fetchone()["today"]
    filename = f"{name}-report-{today.isoformat()}.csv"
    return Response(text, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
