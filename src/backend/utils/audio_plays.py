"""Persistent per-clue audio allowances."""

import psycopg
from fastapi import HTTPException

from database import get_connection
from difficulties import Difficulty
from teacher_access import database_unavailable

_LIMITS = {Difficulty.BASIC: None, Difficulty.ADVANCED: 5, Difficulty.EXPERT: 3}


def play_limit(difficulty):
    return _LIMITS[Difficulty(difficulty)]


def remaining_plays(difficulty, used):
    limit = play_limit(difficulty)
    return None if limit is None else max(0, limit - used)


def consume_play(game_id, student_id, position, difficulty):
    """Reserve one play atomically, including requests from multiple tabs."""
    limit = play_limit(difficulty)
    try:
        with get_connection() as connection:
            # Answers lock the spot before the game; keep that order to avoid deadlocks.
            connection.execute(
                """SELECT position FROM game_session_locations
                WHERE game_session_id = %s AND position = %s FOR UPDATE""", (game_id, position),
            ).fetchone()
            game = connection.execute(
                """SELECT current_position, finished_at FROM game_sessions
                WHERE id = %s AND student_id = %s FOR UPDATE""", (game_id, student_id),
            ).fetchone()
            if game is None:
                raise HTTPException(status_code=404, detail="Game not found")
            if game["finished_at"] or game["current_position"] != position:
                raise HTTPException(status_code=409, detail="This clue is no longer current")
            spot = connection.execute(
                """UPDATE game_session_locations SET audio_plays = audio_plays + 1
                WHERE game_session_id = %s AND position = %s
                    AND (%s::integer IS NULL OR audio_plays < %s)
                RETURNING audio_plays""", (game_id, position, limit, limit),
            ).fetchone()
            if spot is None:
                raise HTTPException(status_code=409, detail="No audio plays remaining for this clue")
            return remaining_plays(difficulty, spot["audio_plays"])
    except (psycopg.Error, RuntimeError):
        raise database_unavailable() from None
