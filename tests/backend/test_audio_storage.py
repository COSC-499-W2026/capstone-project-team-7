from pathlib import Path

import pytest

from utils.audio_storage import (DEFAULT_AUDIO_ROOT, audio_filename, audio_path, audio_root, clip_path, is_mp3,
                                 save_audio, save_clip)

LOCATION = {"building": "COM", "room_number": "316"}
CLIP_ID = "6f1c2a4e-8b3d-4c5e-9f70-1a2b3c4d5e6f"
FRAME = bytes.fromhex("fff364c4")


def test_mp3_with_or_without_id3_tag_is_accepted():
    assert is_mp3(FRAME)
    assert is_mp3(b"ID3\x04\x00\x00\x00\x00\x00\x02ab" + FRAME)


@pytest.mark.parametrize("data", [
    b"", b"not audio", FRAME[:3], b"ID3\x04\x00\x00\x00\x00\x00\x02ab", b"ID3\x04\x00\x00\x00\x00\x00\x02abnot audio",
    bytes.fromhex("fff564c4"),  # Layer II, not an MP3
    bytes.fromhex("ffeb64c4"),  # reserved MPEG version bits
    bytes.fromhex("fff3f4c4"),  # invalid bitrate
    bytes.fromhex("fff36cc4"),  # reserved sample rate
])
def test_other_data_is_not_an_mp3(data):
    assert not is_mp3(data)


def test_save_audio_replaces_the_clip_and_leaves_no_temp_file(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    save_audio("fr", LOCATION, b"old")
    save_audio("fr", LOCATION, b"new")
    assert audio_path("fr", LOCATION).read_bytes() == b"new"
    assert [path.name for path in (tmp_path / "fr").iterdir()] == ["COM-316.mp3"]


def test_save_audio_for_a_difficulty_goes_in_its_folder(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    save_audio("fr", LOCATION, b"expert clip", "expert")
    assert (tmp_path / "fr" / "expert" / "COM-316.mp3").read_bytes() == b"expert clip"
    assert not audio_path("fr", LOCATION).exists()


def test_audio_is_named_by_building_and_room():
    assert audio_filename(LOCATION) == "COM-316.mp3"


def test_audio_folder_comes_from_audio_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    assert audio_path("fr", LOCATION) == tmp_path / "fr" / "COM-316.mp3"


def test_without_audio_dir_audio_stays_in_the_backend(monkeypatch):
    monkeypatch.delenv("AUDIO_DIR", raising=False)
    assert audio_root() == DEFAULT_AUDIO_ROOT
    assert DEFAULT_AUDIO_ROOT.parts[-2:] == ("backend", "audio")


def test_blank_audio_dir_uses_the_default(monkeypatch):
    monkeypatch.setenv("AUDIO_DIR", "")
    assert audio_root() == DEFAULT_AUDIO_ROOT


@pytest.mark.parametrize("difficulty,relative", [
    ("basic", "fr/COM-316.mp3"),
    ("advanced", "fr/advanced/COM-316.mp3"),
    ("expert", "fr/expert/COM-316.mp3"),
])
def test_difficulties_have_separate_audio_paths(monkeypatch, tmp_path, difficulty, relative):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    assert audio_path("fr", LOCATION, difficulty) == tmp_path / relative


def test_invalid_difficulty_cannot_select_an_audio_folder():
    with pytest.raises(ValueError):
        audio_path("fr", LOCATION, "../expert")


def test_extra_clips_have_their_own_folder_by_id(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    assert clip_path("fr", CLIP_ID) == tmp_path / "fr" / "clips" / f"{CLIP_ID}.mp3"


@pytest.mark.parametrize("clip_id", ["", "../COM-316", "not-a-uuid", f"{CLIP_ID}/../x"])
def test_clip_id_must_be_a_uuid_to_build_a_path(clip_id):
    with pytest.raises(ValueError):
        clip_path("fr", clip_id)


def test_save_clip_writes_only_the_clip_file(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    save_clip("fr", CLIP_ID, b"own clip")
    assert clip_path("fr", CLIP_ID).read_bytes() == b"own clip"
    assert [path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")] == [
        "fr", "fr/clips", f"fr/clips/{CLIP_ID}.mp3"]


def test_failed_clip_save_keeps_the_existing_file_and_no_temp_file(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    save_clip("fr", CLIP_ID, b"old")

    def disk_full(self, target):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "replace", disk_full)
    with pytest.raises(OSError):
        save_clip("fr", CLIP_ID, b"new")
    assert clip_path("fr", CLIP_ID).read_bytes() == b"old"
    assert [path.name for path in (tmp_path / "fr" / "clips").iterdir()] == [f"{CLIP_ID}.mp3"]
