"""Clue audio files, kept in the AUDIO_DIR folder (a Docker bind mount), or src/backend/audio without it."""

import os
from pathlib import Path
from uuid import uuid4

DEFAULT_AUDIO_ROOT = Path(__file__).resolve().parents[1] / "audio"
MPEG_VERSION_RESERVED = 1
LAYER_3 = 1
BITRATE_INVALID = 15
SAMPLE_RATE_RESERVED = 3


def audio_root():
    return Path(os.getenv("AUDIO_DIR") or DEFAULT_AUDIO_ROOT)


def audio_filename(location):
    """Named by building and room (not id) because ids differ in each database."""
    return f"{location['building']}-{location['room_number']}.mp3"


def audio_path(language_code, location):
    return audio_root() / language_code / audio_filename(location)


def id3_tag_length(data):
    """Bytes of ID3v2 metadata before the audio; each size byte holds only 7 bits."""
    if data[:3] != b"ID3" or len(data) < 10:
        return 0
    size = data[6] << 21 | data[7] << 14 | data[8] << 7 | data[9]
    footer = 10 if data[5] & 0x10 else 0
    return 10 + size + footer


def is_mp3(data):
    """True when the audio starts with a valid MPEG Layer III frame header."""
    start = id3_tag_length(data)
    header = data[start:start + 4]
    if len(header) < 4 or header[0] != 0xFF or header[1] & 0xE0 != 0xE0:
        return False
    return ((header[1] >> 3) & 3 != MPEG_VERSION_RESERVED
            and (header[1] >> 1) & 3 == LAYER_3
            and header[2] >> 4 != BITRATE_INVALID
            and (header[2] >> 2) & 3 != SAMPLE_RATE_RESERVED)


def save_audio(language_code, location, data):
    """Swap in a finished temp file, so a failed write leaves any existing clip playing."""
    path = audio_path(language_code, location)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{uuid4().hex}.tmp")
    try:
        temp.write_bytes(data)
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
