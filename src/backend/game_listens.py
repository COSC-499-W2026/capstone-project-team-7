"""Count how many times a student presses play on a clue's audio."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from game_session import current_location
from student_enrollment import require_student
from teacher_access import database_unavailable

router = APIRouter(prefix="/api/game", tags=["game"])


@router.post("/{game_id}/listen", summary="Count one play of the current clue's audio")
def listen(game_id: UUID, position: int | None = None, clue_id: UUID | None = None,
           user=Depends(require_student)):
    # Same checks as the other game endpoints: 404 if the game is missing or someone else's, 409 if it has ended.
    current_location(game_id, user["id"])
    try:
        with get_connection() as connection:
            # Adding 1 inside the database means two plays at the same moment are both counted.
            spot = connection.execute(
                """UPDATE game_session_locations SET listens = listens + 1
                FROM game_sessions
                WHERE game_sessions.id = game_session_locations.game_session_id
                    AND game_session_locations.position = game_sessions.current_position
                    AND game_session_locations.position = COALESCE(%s, game_sessions.current_position)
                    AND game_session_locations.location_id = COALESCE(%s, game_session_locations.location_id)
                    AND game_sessions.id = %s AND game_sessions.student_id = %s
                    AND game_sessions.finished_at IS NULL AND game_sessions.quit_at IS NULL
                RETURNING game_session_locations.position, game_session_locations.listens""",
                (position, clue_id, game_id, user["id"]),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if spot is None:
        raise HTTPException(status_code=409, detail="The clue is no longer current")
    return spot
