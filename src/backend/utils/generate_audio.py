"""Make the French audio clue for each demo location with: cd src/backend && python -m utils.generate_audio.

Needs the edge-tts package on your computer (pip install edge-tts). It's only used to make the
files once, so it isn't in requirements.txt. Files are saved in the backend, which plays them to
students through the game API so the file names (which contain room numbers) stay hidden.
"""

import asyncio
from pathlib import Path

from utils.seed_locations import LOCATIONS

AUDIO_FOLDER = Path(__file__).resolve().parents[1] / "audio" / "fr"
VOICE = "fr-FR-DeniseNeural"


def audio_filename(location):
    """Named by building and room (not id) because ids differ in each database."""
    return f"{location['building']}-{location['room_number']}.mp3"


async def make_audio(text, path):
    import edge_tts  # imported here so tests can run without it installed

    await edge_tts.Communicate(text, VOICE).save(str(path))


if __name__ == "__main__":
    AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
    for location in LOCATIONS:
        path = AUDIO_FOLDER / audio_filename(location)
        number_text, _ = location["fr"]
        asyncio.run(make_audio(number_text, path))  # Basic difficulty: the room number only
        print(f"Saved {path.name}")
