"""Make the French audio clue for each demo location with: cd src/backend && python -m utils.generate_audio.

Needs the edge-tts package on your computer (pip install edge-tts). It's only used to make the
files once, so it isn't in requirements.txt. Files are saved in the audio folder (see audio_storage),
which the backend plays to students through the game API so the file names (which contain room numbers)
stay hidden.
"""

import asyncio

from utils.audio_storage import audio_path
from utils.seed_locations import LOCATIONS

VOICE = "fr-FR-DeniseNeural"


async def make_audio(text, path):
    import edge_tts  # imported here so tests can run without it installed

    await edge_tts.Communicate(text, VOICE).save(str(path))


if __name__ == "__main__":
    for location in LOCATIONS:
        path = audio_path("fr", location)
        path.parent.mkdir(parents=True, exist_ok=True)
        number_text, _ = location["fr"]
        asyncio.run(make_audio(number_text, path))  # Basic difficulty: the room number only
        print(f"Saved {path.name}")
