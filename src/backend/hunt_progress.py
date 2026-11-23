"""Playing assigned hunts: a student starts a game for a hunt, and the teacher sees who completed it."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from game_session import StartGameRequest, create_game
from student_enrollment import require_student
from teacher_access import database_unavailable, owned_class, teacher_connection

router = APIRouter(prefix="/api", tags=["hunts"])


@router.post("/student/hunts/{hunt_id}/start", status_code=201, summary="Start a game for one of your assigned hunts")
def start_hunt(hunt_id: UUID, user=Depends(require_student)):
    try:
        with get_connection() as connection:
            hunt = connection.execute(
                """SELECT assigned_hunts.language_code, assigned_hunts.difficulty FROM assigned_hunts
                JOIN class_enrollments ON class_enrollments.class_id = assigned_hunts.class_id
                WHERE assigned_hunts.id = %s AND class_enrollments.student_id = %s
                    AND class_enrollments.status = 'enrolled'""",
                (hunt_id, user["id"]),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    # A hunt for a class you're not in looks the same as a missing one, so hunts can't be peeked at.
    if hunt is None:
        raise HTTPException(status_code=404, detail="Hunt not found")
    settings = StartGameRequest(language_code=hunt["language_code"], difficulty=hunt["difficulty"])
    return create_game(user["id"], settings, hunt_id)


@router.get("/teacher/hunts/{hunt_id}/completion", summary="Each enrolled student's progress on one of your hunts")
def hunt_completion(hunt_id: UUID, access=Depends(teacher_connection)):
    connection, teacher_id = access
    hunt = connection.execute("SELECT class_id FROM assigned_hunts WHERE id = %s", (hunt_id,)).fetchone()
    # Another teacher's hunt looks the same as a missing one.
    if hunt is None or not owned_class(connection, hunt["class_id"], teacher_id):
        raise HTTPException(status_code=404, detail="Hunt not found")
    # Quit games are left out of the join, so they never count as completed or in progress.
    return connection.execute(
        """SELECT users.username,
            CASE WHEN COUNT(game_sessions.finished_at) > 0 THEN 'completed'
                WHEN COUNT(game_sessions.id) > 0 THEN 'in_progress' ELSE 'not_started' END AS status,
            MAX(game_sessions.points) FILTER (WHERE game_sessions.finished_at IS NOT NULL) AS best_points,
            MIN(FLOOR(EXTRACT(EPOCH FROM game_sessions.finished_at - game_sessions.started_at))::int) AS fastest_time
        FROM class_enrollments
        JOIN users ON users.id = class_enrollments.student_id
        LEFT JOIN game_sessions ON game_sessions.student_id = class_enrollments.student_id
            AND game_sessions.hunt_id = %s AND game_sessions.quit_at IS NULL
        WHERE class_enrollments.class_id = %s AND class_enrollments.status = 'enrolled'
        GROUP BY users.id, users.username
        ORDER BY users.username""",
        (hunt_id, hunt["class_id"]),
    ).fetchall()
