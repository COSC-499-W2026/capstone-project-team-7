import pytest

from utils.audio_storage import DEFAULT_AUDIO_ROOT, audio_filename, audio_path, audio_root, is_mp3, save_audio

LOCATION = {"building": "COM", "room_number": "316"}
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
