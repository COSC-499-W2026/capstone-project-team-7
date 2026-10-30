"""Students start a game: five random locations in a fixed order."""

from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from database import get_connection
from difficulties import Difficulty
from student_enrollment import require_student
from teacher_access import database_unavailable
from utils.answer_check import check_answer
from utils.ocr import InvalidPhoto, MAX_PHOTO_BYTES, OCRUnavailable
from utils.audio_storage import audio_path
from utils.location_picker import LOCATIONS_PER_HUNT, NotEnoughLocations, pick_locations

router = APIRouter(prefix="/api/game", tags=["game"])

# The demo game is always French Basic until students can choose.
LANGUAGE = "fr"
DIFFICULTY = Difficulty.BASIC
POINTS_PER_LOCATION = 10


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


def current_location(game_id, student_id):
    """The location at the game's current position, or a 404/409/503 error."""
    try:
        with get_connection() as connection:
            location = connection.execute(
                """SELECT game_sessions.language_code, game_sessions.current_position, game_sessions.finished_at,
                locations.building, locations.room_number
                FROM game_sessions
                JOIN game_session_locations ON game_session_locations.game_session_id = game_sessions.id
                    AND game_session_locations.position = game_sessions.current_position
                JOIN locations ON locations.id = game_session_locations.location_id
                WHERE game_sessions.id = %s AND game_sessions.student_id = %s""",
                (game_id, student_id),
            ).fetchone()
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    # Another student's game looks the same as a missing one, so games can't be peeked at.
    if location is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if location["finished_at"]:
        raise HTTPException(status_code=409, detail="This game is already finished")
    return location


@router.get("/{game_id}/clue", summary="The current clue: the building and where to get its audio")
def current_clue(game_id: UUID, user=Depends(require_student)):
    location = current_location(game_id, user["id"])
    # The room number is never sent as text, and the audio link doesn't contain it either.
    return {
        "position": location["current_position"],
        "total_locations": LOCATIONS_PER_HUNT,
        "building": location["building"],
        "audio_url": f"/api/game/{game_id}/clue/audio?position={location['current_position']}",
    }


@router.get("/{game_id}/clue/audio", summary="Play the audio for the current clue")
def current_clue_audio(game_id: UUID, user=Depends(require_student)):
    location = current_location(game_id, user["id"])
    path = audio_path(location["language_code"], location)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found for this clue")
    return FileResponse(path, media_type="audio/mpeg")


async def read_photo(request: Request):
    """The photo sent as the request body (e.g. image/jpeg)."""
    photo = bytearray()
    async for chunk in request.stream():
        if len(photo) + len(chunk) > MAX_PHOTO_BYTES:
            raise HTTPException(status_code=413, detail="Photo is too large")
        photo.extend(chunk)
    if not photo:
        raise HTTPException(status_code=422, detail="Please take a photo of the room number")
    return bytes(photo)


@router.post("/{game_id}/answer", summary="Submit a photo for the current spot")
def submit_answer(game_id: UUID, user=Depends(require_student), photo=Depends(read_photo)):
    location = current_location(game_id, user["id"])
    position = location["current_position"]
    try:
        correct = check_answer(photo, location)
    except InvalidPhoto as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except OCRUnavailable:
        raise HTTPException(status_code=503, detail="Photo recognition is unavailable. Please try again later.") from None
    awarded = POINTS_PER_LOCATION if correct else 0
    try:
        with get_connection() as connection:
            # Gate both correct and incorrect submissions on the target that OCR checked.
            game = connection.execute(
                """UPDATE game_sessions
                SET current_position = LEAST(current_position + %s, %s), points = points + %s,
                    finished_at = CASE WHEN %s AND current_position = %s THEN now() ELSE finished_at END
                WHERE id = %s AND student_id = %s AND current_position = %s AND finished_at IS NULL
                RETURNING current_position, finished_at, points""",
                (int(correct), LOCATIONS_PER_HUNT, awarded, correct, LOCATIONS_PER_HUNT,
                 game_id, user["id"], position),
            ).fetchone()
            if game is None:
                raise HTTPException(status_code=409, detail="This spot was already answered")
            spot = connection.execute(
                """UPDATE game_session_locations
                SET attempts = attempts + 1, found_at = CASE WHEN %s THEN now() ELSE found_at END
                WHERE game_session_id = %s AND position = %s AND found_at IS NULL RETURNING attempts""",
                (correct, game_id, position),
            ).fetchone()
            if spot is None:
                raise HTTPException(status_code=409, detail="This spot was already answered")
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
    finished = bool(game["finished_at"])
    return {
        "correct": correct,
        "attempts": spot["attempts"],
        "finished": finished,
        "next_position": game["current_position"] if correct and not finished else None,
        "points_awarded": awarded,
        "total_points": game["points"],
        "message": "Correct room!" if correct else "The room number is incorrect or unreadable. Please retake the photo.",
    }
