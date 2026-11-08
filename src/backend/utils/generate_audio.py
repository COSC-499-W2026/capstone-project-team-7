"""Make French demo audio for all difficulties: cd src/backend && python -m utils.generate_audio.

Needs the edge-tts package on your computer (pip install edge-tts). It's only used to make the
files once, so it isn't in requirements.txt. Files are saved in the audio folder (see audio_storage),
which the backend plays to students through the game API so the file names (which contain room numbers)
stay hidden.
"""

import asyncio

from difficulties import Difficulty
from utils.audio_storage import audio_path
from utils.clue_text import clue_text
from utils.seed_locations import LOCATIONS

VOICE = "fr-FR-DeniseNeural"


async def make_audio(text, path):
    import edge_tts  # imported here so tests can run without it installed

    await edge_tts.Communicate(text, VOICE).save(str(path))


async def generate_audio(locations=LOCATIONS):
    """Generate a separate clip for every demo location and difficulty."""
    for location in locations:
        number_text, description_text = location["fr"]
        for difficulty in Difficulty:
            text = clue_text(number_text, description_text, difficulty)
            path = audio_path("fr", location, difficulty)
            path.parent.mkdir(parents=True, exist_ok=True)
            await make_audio(text, path)
            print(f"Saved {path}")


if __name__ == "__main__":
    asyncio.run(generate_audio())
