"""Class rankings from completed games in the class's language."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/student/classes", tags=["student"])


def class_rankings(connection, class_id, language_code):
    return connection.execute(
        """WITH scores AS (
            SELECT u.username, s.equipped_icon_id AS profile_icon,
                   COALESCE(SUM(g.points), 0) AS total_points
            FROM class_enrollments e
            JOIN users u ON u.id = e.student_id
            JOIN students s ON s.user_id = e.student_id
            LEFT JOIN game_sessions g ON g.student_id = e.student_id
                AND g.language_code = %s AND g.finished_at IS NOT NULL
            WHERE e.class_id = %s AND e.status = 'enrolled'
            GROUP BY u.id, s.equipped_icon_id
        ) SELECT RANK() OVER (ORDER BY total_points DESC) AS rank,
                 username, total_points, profile_icon
          FROM scores ORDER BY total_points DESC, lower(username), username""",
        (language_code, class_id),
    ).fetchall()


@router.get("/{class_id}/leaderboard", summary="Read your class leaderboard with equipped icons")
def leaderboard(class_id: UUID, user=Depends(require_student)):
    try:
        with get_connection() as connection:
            classroom = connection.execute(
                "SELECT language_code FROM classes WHERE id = %s", (class_id,),
            ).fetchone()
            if classroom is None:
                raise HTTPException(status_code=404, detail="Class not found")
            enrolled = connection.execute(
                """SELECT 1 FROM class_enrollments
                WHERE class_id = %s AND student_id = %s AND status = 'enrolled'""",
                (class_id, user["id"]),
            ).fetchone()
            if enrolled is None:
                raise HTTPException(status_code=403, detail="You must be enrolled in this class")
            return class_rankings(connection, class_id, classroom["language_code"])
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
