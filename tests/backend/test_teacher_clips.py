from uuid import uuid4

import pytest

import teacher_access
import teacher_clips
import teacher_locations
from database import get_connection
from test_teacher_access import access_db, client, login
from test_teacher_locations import COM, MP3, add_location, audio_dir, locations_url
from utils.audio_storage import audio_path, clip_path

CLIP = {"difficulty": "basic", "label": "Café clue"}


def clips_url(class_id):
    return f"/api/teacher/classes/{class_id}/clips"


def add_clip(client, class_id, location_id, data=MP3, **params):
    return client.post(f"{locations_url(class_id)}/{location_id}/clips", content=data,
                       params={**CLIP, **params}, headers={"Content-Type": "audio/mpeg"})


def add_class(username, language_code):
    with get_connection() as db:
        return str(db.execute("""INSERT INTO classes (teacher_id, name, language_code)
            SELECT id, 'Another class', %s FROM users WHERE username = %s RETURNING id""",
                              (language_code, username)).fetchone()["id"])


def class_of(username):
    with get_connection() as db:
        return str(db.execute("""SELECT classes.id FROM classes JOIN users ON users.id = classes.teacher_id
            WHERE users.username = %s""", (username,)).fetchone()["id"])


def clip_rows():
    with get_connection() as db:
        return db.execute("SELECT label, retired_at IS NOT NULL AS retired FROM location_clips").fetchall()


def test_added_clip_is_saved_and_listed_with_its_label(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    response = add_clip(client, access_db, location_id, description="Next to the café")
    assert response.status_code == 201
    clip = response.json()
    assert clip == {"id": clip["id"], "location_id": location_id, **COM, "difficulty": "basic",
                    "label": "Café clue", "description": "Next to the café", "created_at": clip["created_at"]}
    assert clip_path("fr", clip["id"]).read_bytes() == MP3
    assert not audio_path("fr", COM).exists()
    assert client.get(clips_url(access_db)).json() == [clip]


def test_label_and_description_are_trimmed_and_description_is_optional(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    clip = add_clip(client, access_db, location_id, label="  Café clue  ").json()
    assert (clip["label"], clip["description"]) == ("Café clue", None)


def test_list_is_newest_first_and_filters_by_difficulty(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    basic = add_clip(client, access_db, location_id).json()
    expert = add_clip(client, access_db, location_id, difficulty="expert", label="Hard clue").json()
    assert [clip["id"] for clip in client.get(clips_url(access_db)).json()] == [expert["id"], basic["id"]]
    assert client.get(clips_url(access_db), params={"difficulty": "expert"}).json() == [expert]
    assert client.get(clips_url(access_db), params={"difficulty": "advanced"}).json() == []


def test_own_clips_show_in_every_class_of_the_same_language_only(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    other_french, spanish = add_class("teacher", "fr"), add_class("teacher", "es")
    login(client)
    clip = add_clip(client, access_db, location_id).json()
    assert client.get(clips_url(other_french)).json() == [clip]
    assert client.get(clips_url(spanish)).json() == []


def test_other_teachers_never_see_or_use_a_clip(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    clip_id = add_clip(client, access_db, location_id).json()["id"]
    login(client, "teacher2")
    own_class = class_of("teacher2")
    assert client.get(clips_url(own_class)).json() == []
    for response in (client.get(f"{clips_url(own_class)}/{clip_id}/audio"),
                     client.delete(f"{clips_url(own_class)}/{clip_id}")):
        assert response.status_code == 404
        assert response.json() == {"detail": "Clip not found"}
    assert clip_rows() == [{"label": "Café clue", "retired": False}]


def test_other_teachers_class_is_not_found(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client, "teacher2")
    assert add_clip(client, access_db, location_id).status_code == 404
    assert client.get(clips_url(access_db)).status_code == 404
    assert clip_rows() == []


def test_teacher_plays_their_own_clip(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    clip_id = add_clip(client, access_db, location_id).json()["id"]
    response = client.get(f"{clips_url(access_db)}/{clip_id}/audio")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == MP3


def test_clip_with_a_missing_file_is_not_found(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    clip_id = add_clip(client, access_db, location_id).json()["id"]
    clip_path("fr", clip_id).unlink()
    assert client.get(f"{clips_url(access_db)}/{clip_id}/audio").status_code == 404


def test_retired_clip_is_hidden_but_kept(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    clip_id = add_clip(client, access_db, location_id).json()["id"]
    assert client.delete(f"{clips_url(access_db)}/{clip_id}").status_code == 204
    assert client.get(clips_url(access_db)).json() == []
    assert client.get(f"{clips_url(access_db)}/{clip_id}/audio").status_code == 404
    assert client.delete(f"{clips_url(access_db)}/{clip_id}").status_code == 404
    assert clip_rows() == [{"label": "Café clue", "retired": True}]
    assert clip_path("fr", clip_id).exists()


def test_unknown_clip_is_not_found(access_db, audio_dir, client):
    login(client)
    assert client.delete(f"{clips_url(access_db)}/{uuid4()}").status_code == 404
    assert client.get(f"{clips_url(access_db)}/{uuid4()}/audio").status_code == 404


@pytest.mark.parametrize("params", [
    {"difficulty": "hard"}, {"difficulty": None}, {"label": ""}, {"label": "   "}, {"label": None},
    {"label": "x" * 61}, {"description": ""}, {"description": "x" * 301}, {"extra": "field"},
])
def test_invalid_clip_details_are_rejected_and_nothing_is_saved(access_db, audio_dir, client, params):
    location_id = add_location("COM", "316")
    login(client)
    query = {key: value for key, value in {**CLIP, **params}.items() if value is not None}
    response = client.post(f"{locations_url(access_db)}/{location_id}/clips", content=MP3, params=query,
                           headers={"Content-Type": "audio/mpeg"})
    assert response.status_code == 422
    assert clip_rows() == []
    assert not any(audio_dir.rglob("*.mp3"))


def test_longest_label_and_description_are_accepted(access_db, audio_dir, client):
    location_id = add_location("COM", "316")
    login(client)
    assert add_clip(client, access_db, location_id, label="x" * 60, description="y" * 300).status_code == 201


@pytest.mark.parametrize("data", [b"not an mp3", b""])
def test_non_mp3_is_rejected_and_nothing_is_saved(access_db, audio_dir, client, data):
    location_id = add_location("COM", "316")
    login(client)
    response = add_clip(client, access_db, location_id, data)
    assert response.status_code == 422
    assert response.json() == {"detail": "Please upload an MP3 file"}
    assert clip_rows() == []


def test_too_large_clip_is_rejected(access_db, audio_dir, client, monkeypatch):
    monkeypatch.setattr(teacher_locations, "MAX_AUDIO_BYTES", len(MP3) - 1)
    location_id = add_location("COM", "316")
    login(client)
    assert add_clip(client, access_db, location_id).status_code == 413
    assert clip_rows() == []


def test_unknown_location_or_other_language_is_not_found(access_db, audio_dir, client):
    spanish_only = add_location("ART", "100", "es")
    login(client)
    for location_id in (uuid4(), spanish_only):
        response = add_clip(client, access_db, location_id)
        assert response.status_code == 404
        assert response.json() == {"detail": "Location not found"}
    assert clip_rows() == []


def test_missing_session_and_students_are_rejected(access_db, audio_dir, client):
    clip_id = uuid4()
    requests = (lambda: add_clip(client, access_db, uuid4()),
                lambda: client.get(clips_url(access_db)),
                lambda: client.get(f"{clips_url(access_db)}/{clip_id}/audio"),
                lambda: client.delete(f"{clips_url(access_db)}/{clip_id}"))
    assert [request().status_code for request in requests] == [401] * 4
    login(client, "student")
    assert [request().status_code for request in requests] == [403] * 4


def test_database_failure_returns_503(access_db, audio_dir, client, monkeypatch):
    location_id = add_location("COM", "316")
    login(client)

    def unavailable():
        raise RuntimeError("database down")

    for module in (teacher_access, teacher_locations, teacher_clips):
        monkeypatch.setattr(module, "get_connection", unavailable)
    responses = (add_clip(client, access_db, location_id), client.get(clips_url(access_db)),
                 client.get(f"{clips_url(access_db)}/{uuid4()}/audio"),
                 client.delete(f"{clips_url(access_db)}/{uuid4()}"))
    for response in responses:
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}


def test_failed_insert_returns_503_and_saves_no_file(access_db, audio_dir, client, monkeypatch):
    location_id = add_location("COM", "316")
    login(client)

    def unavailable():
        raise RuntimeError("database down")

    monkeypatch.setattr(teacher_clips, "get_connection", unavailable)
    assert add_clip(client, access_db, location_id).status_code == 503
    assert not any(audio_dir.rglob("*.mp3"))


def test_failed_file_save_returns_503_and_leaves_no_clip(access_db, audio_dir, client, monkeypatch):
    location_id = add_location("COM", "316")
    login(client)

    def disk_full(*_):
        raise OSError("disk full")

    monkeypatch.setattr(teacher_clips, "save_clip", disk_full)
    response = add_clip(client, access_db, location_id)
    assert response.status_code == 503
    assert response.json() == {"detail": "Could not save the audio, please try again"}
    assert clip_rows() == []
