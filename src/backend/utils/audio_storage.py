"""Where clue audio is kept: the AUDIO_DIR folder (a Docker bind mount), or src/backend/audio without it."""

import os
from pathlib import Path

from difficulties import Difficulty

DEFAULT_AUDIO_ROOT = Path(__file__).resolve().parents[1] / "audio"


def audio_root():
    return Path(os.getenv("AUDIO_DIR") or DEFAULT_AUDIO_ROOT)


def audio_filename(location):
    """Named by building and room (not id) because ids differ in each database."""
    return f"{location['building']}-{location['room_number']}.mp3"


def audio_path(language_code, location, difficulty=Difficulty.BASIC):
    level = Difficulty(difficulty)
    folder = audio_root() / language_code
    # Keep existing Basic clips usable by the game and teacher uploads.
    if level != Difficulty.BASIC:
        folder = folder / level.value
    return folder / audio_filename(location)
