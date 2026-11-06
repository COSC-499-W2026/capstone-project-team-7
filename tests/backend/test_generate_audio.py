import asyncio

import pytest

from utils import generate_audio
from utils.audio_storage import audio_filename
from utils.seed_locations import LOCATIONS


def test_every_demo_location_gets_its_own_file():
    names = {audio_filename(location) for location in LOCATIONS}
    assert len(names) == 5


def test_generates_distinct_clips_with_each_levels_content(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    saved = {}

    async def save(text, path):
        assert path.parent.is_dir()
        saved[path.relative_to(tmp_path).as_posix()] = text

    monkeypatch.setattr(generate_audio, "make_audio", save)
    asyncio.run(generate_audio.generate_audio())
    assert len(saved) == len(LOCATIONS) * 3
    for location in LOCATIONS:
        number, description = location["fr"]
        filename = audio_filename(location)
        assert saved[f"fr/{filename}"] == number
        assert saved[f"fr/advanced/{filename}"] == f"{number}. {description}"
        assert saved[f"fr/expert/{filename}"] == description


def test_generation_failure_is_reported(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))

    async def unavailable(text, path):
        raise RuntimeError("Speech service unavailable")

    monkeypatch.setattr(generate_audio, "make_audio", unavailable)
    with pytest.raises(RuntimeError, match="Speech service unavailable"):
        asyncio.run(generate_audio.generate_audio(LOCATIONS[:1]))
