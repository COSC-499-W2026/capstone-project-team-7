from uuid import uuid4

import pytest

import teacher_access
import teacher_locations
from database import get_connection
from test_teacher_access import access_db, client, login
from utils.audio_storage import audio_path

MP3 = bytes.fromhex("fff364c4") + b"new clip"
OLD_CLIP = bytes.fromhex("fff364c4") + b"old clip"
COM = {"building": "COM", "room_number": "316"}


@pytest.fixture
def audio_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    return tmp_path


def add_location(building, room_number, language_code="fr"):
    with get_connection() as db:
        location_id = db.execute("INSERT INTO locations (building, room_number) VALUES (%s, %s) RETURNING id",
                                 (building, room_number)).fetchone()["id"]
        db.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
                   VALUES (%s, %s, 'number', 'description')""", (location_id, language_code))
    return str(location_id)


def add_old_clip():
    path = audio_path("fr", COM)
    path.parent.mkdir(parents=True)
    path.write_bytes(OLD_CLIP)
    return path


def locations_url(class_id):
    return f"/api/teacher/classes/{class_id}/locations"


def upload(client, class_id, location_id, data=MP3):
    return client.put(f"{locations_url(class_id)}/{location_id}/audio", content=data,
                      headers={"Content-Type": "audio/mpeg"})


def test_list_shows_class_language_locations_and_audio_status(access_db, audio_dir, client):
    com = add_location("COM", "316")
    lib = add_location("LIB", "312")
    add_location("ART", "100", "es")
    add_old_clip()
    login(client)
    response = client.get(locations_url(access_db))
    assert response.status_code == 200
    assert response.json() == [
        {"id": com, "building": "COM", "room_number": "316", "has_audio": True},
        {"id": lib, "building": "LIB", "room_number": "312", "has_audio": False},
    ]


def test_list_without_locations_is_empty(access_db, audio_dir, client):
    login(client)
    assert client.get(locations_url(access_db)).json() == []


def test_upload_adds_a_clip_and_marks_the_location(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    response = upload(client, access_db, location_id)
    assert response.status_code == 200
    assert response.json() == {"id": location_id, **COM, "has_audio": True}
    assert audio_path("fr", COM).read_bytes() == MP3


def test_upload_replaces_an_existing_clip(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    path = add_old_clip()
    login(client)
    assert upload(client, access_db, location_id).status_code == 200
    assert path.read_bytes() == MP3


@pytest.mark.parametrize("data", [b"not an mp3", b""])
def test_invalid_upload_keeps_the_existing_clip(access_db, audio_dir, client, data):
    location_id = add_location("COM", "316")
    path = add_old_clip()
    login(client)
    response = upload(client, access_db, location_id, data)
    assert response.status_code == 422
    assert response.json() == {"detail": "Please upload an MP3 file"}
    assert path.read_bytes() == OLD_CLIP


def test_too_large_upload_is_rejected(access_db, audio_dir, client, monkeypatch):
    monkeypatch.setattr(teacher_locations, "MAX_AUDIO_BYTES", len(MP3) - 1)
    location_id = add_location("COM", "316")
    login(client)
    assert upload(client, access_db, location_id).status_code == 413
    assert not audio_path("fr", COM).exists()


def test_other_teachers_class_is_not_found(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client, "teacher2")
    assert client.get(locations_url(access_db)).status_code == 404
    assert upload(client, access_db, location_id).status_code == 404
    assert not audio_path("fr", COM).exists()


def test_unknown_location_or_other_language_is_not_found(access_db, audio_dir, client):
    spanish_only = add_location("ART", "100", "es")
    login(client)
    for location_id in (uuid4(), spanish_only):
        response = upload(client, access_db, location_id)
        assert response.status_code == 404
        assert response.json() == {"detail": "Location not found"}


def test_missing_session_is_rejected(access_db, audio_dir, client):
    assert client.get(locations_url(access_db)).status_code == 401
    assert upload(client, access_db, uuid4()).status_code == 401


def test_students_are_forbidden(access_db, audio_dir, client):
    login(client, "student")
    assert client.get(locations_url(access_db)).status_code == 403
    assert upload(client, access_db, uuid4()).status_code == 403


def test_database_failure_returns_503(access_db, audio_dir, client, monkeypatch):
    location_id = add_location("COM", "316")
    login(client)

    def unavailable():
        raise RuntimeError("database down")

    monkeypatch.setattr(teacher_access, "get_connection", unavailable)
    monkeypatch.setattr(teacher_locations, "get_connection", unavailable)
    assert client.get(locations_url(access_db)).status_code == 503
    assert upload(client, access_db, location_id).status_code == 503


def test_failed_save_returns_503_and_keeps_the_clip(access_db, audio_dir, client, monkeypatch):
    location_id = add_location("COM", "316")
    path = add_old_clip()
    login(client)

    def disk_full(*_):
        raise OSError("disk full")

    monkeypatch.setattr(teacher_locations, "save_audio", disk_full)
    response = upload(client, access_db, location_id)
    assert response.status_code == 503
    assert path.read_bytes() == OLD_CLIP
