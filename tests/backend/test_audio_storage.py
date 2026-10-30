from utils.audio_storage import DEFAULT_AUDIO_ROOT, audio_filename, audio_path, audio_root

LOCATION = {"building": "COM", "room_number": "316"}


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
