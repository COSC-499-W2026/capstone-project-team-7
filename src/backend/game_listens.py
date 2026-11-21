"""Count how many times a student presses play on a clue's audio."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from database import get_connection
from student_enrollment import require_student
from teacher_access import database_unavailable
from utils.location_picker import LOCATIONS_PER_HUNT

router = APIRouter(prefix="/api/game", tags=["game"])


class ListenRequest(BaseModel):
    """Which clue was played, so a slow request still counts for the right clue."""

    model_config = ConfigDict(extra="forbid")
    position: int = Field(ge=1, le=LOCATIONS_PER_HUNT)


@router.post("/{game_id}/listen", summary="Count one play of a clue's audio")
def listen(game_id: UUID, info: ListenRequest, user=Depends(require_student)):
    try:
        with get_connection() as connection:
            # Adding 1 inside the database means two plays at the same moment are both counted.
            # A game that finished in the last minute still counts, so a slow request for the last clue isn't lost.
            spot = connection.execute(
                """UPDATE game_session_locations SET listens = listens + 1
                FROM game_sessions
                WHERE game_sessions.id = game_session_locations.game_session_id
                    AND game_session_locations.position = %s
                    AND game_session_locations.position <= game_sessions.current_position
                    AND game_sessions.id = %s AND game_sessions.student_id = %s
                    AND game_sessions.quit_at IS NULL
                    AND (game_sessions.finished_at IS NULL OR game_sessions.finished_at > now() - interval '1 minute')
                RETURNING game_session_locations.position, game_session_locations.listens""",
                (info.position, game_id, user["id"]),
            ).fetchone()
            if spot is None:
                game = connection.execute(
                    "SELECT finished_at, quit_at FROM game_sessions WHERE id = %s AND student_id = %s", (game_id, user["id"]),
                ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    if spot is not None:
        return spot
    # Another student's game looks the same as a missing one, so games can't be peeked at.
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if game["quit_at"]:
        raise HTTPException(status_code=409, detail="This game was quit")
    if game["finished_at"]:
        raise HTTPException(status_code=409, detail="This game is already finished")
    raise HTTPException(status_code=422, detail="You haven't reached that clue yet")
