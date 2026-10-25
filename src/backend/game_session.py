"""Students start a game: five random locations in a fixed order."""

import psycopg
from fastapi import APIRouter, Depends, HTTPException

from database import get_connection
from difficulties import Difficulty
from student_enrollment import require_student
from teacher_access import database_unavailable
from utils.location_picker import LOCATIONS_PER_HUNT, NotEnoughLocations, pick_locations

router = APIRouter(prefix="/api/game", tags=["game"])

# The demo game is always French Basic until students can choose.
LANGUAGE = "fr"
DIFFICULTY = Difficulty.BASIC


@router.post("/start", status_code=201, summary="Start a game with five random locations")
def start_game(user=Depends(require_student)):
    try:
        with get_connection() as connection:
            # Only locations with a clue in this language, so no clue is ever blank.
            rows = connection.execute(
                "SELECT location_id FROM location_clues WHERE language_code = %s", (LANGUAGE,),
            ).fetchall()
            location_ids = pick_locations([row["location_id"] for row in rows])
            game = connection.execute(
                """INSERT INTO game_sessions (student_id, language_code, difficulty)
                VALUES (%s, %s, %s) RETURNING id, language_code, difficulty, current_position""",
                (user["id"], LANGUAGE, DIFFICULTY.value),
            ).fetchone()
            for position, location_id in enumerate(location_ids, start=1):
                connection.execute(
                    """INSERT INTO game_session_locations (game_session_id, position, location_id)
                    VALUES (%s, %s, %s)""",
                    (game["id"], position, location_id),
                )
    except NotEnoughLocations:
        raise HTTPException(status_code=409, detail="Not enough locations for this language yet") from None
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    # Locations stay hidden so the response does not give away the answers.
    return {
        "game_id": game["id"],
        "language_code": game["language_code"],
        "difficulty": game["difficulty"],
        "current_position": game["current_position"],
        "total_locations": LOCATIONS_PER_HUNT,
    }
