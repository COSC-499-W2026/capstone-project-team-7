from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import auth
import game_session
from main import app

GAME_ID = uuid4()
URL = f"/api/game/{GAME_ID}/clue/audio"


@pytest.fixture
def audio_client(monkeypatch, tmp_path):
    user = {"id": uuid4(), "role": "student"}
    app.dependency_overrides[auth.current_user] = lambda: user
    monkeypatch.setenv("AUDIO_DIR", str(tmp_path))
    for difficulty, folder in (("basic", "fr"), ("advanced", "fr/advanced"), ("expert", "fr/expert")):
        path = tmp_path / folder / "COM-316.mp3"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(difficulty.encode())
    with TestClient(app) as client:
        yield client, user
    app.dependency_overrides.clear()


def set_location(monkeypatch, difficulty, user):
    def location(game_id, student_id):
        assert game_id == GAME_ID
        assert student_id == user["id"]
        return {"language_code": "fr", "building": "COM", "room_number": "316", "difficulty": difficulty}
    monkeypatch.setattr(game_session, "current_location", location)


@pytest.mark.parametrize("difficulty", ["basic", "advanced", "expert"])
def test_playback_uses_saved_difficulty(audio_client, monkeypatch, difficulty):
    client, user = audio_client
    set_location(monkeypatch, difficulty, user)
    response = client.get(URL + "?difficulty=basic")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == difficulty.encode()


@pytest.mark.parametrize("difficulty,folder", [("basic", "fr"), ("advanced", "fr/advanced"), ("expert", "fr/expert")])
def test_missing_clip_does_not_fall_back(audio_client, monkeypatch, tmp_path, difficulty, folder):
    client, user = audio_client
    set_location(monkeypatch, difficulty, user)
    (tmp_path / folder / "COM-316.mp3").unlink()
    response = client.get(URL)
    assert response.status_code == 404
    assert response.json() == {"detail": "Audio not found for this clue"}


def test_invalid_saved_difficulty_is_a_safe_error(audio_client, monkeypatch):
    client, user = audio_client
    set_location(monkeypatch, "../basic", user)
    response = client.get(URL)
    assert response.status_code == 500
    assert response.json() == {"detail": "Could not select clue audio. Please try again later."}


@pytest.mark.parametrize("status,detail", [(404, "Game not found"), (409, "This game is already finished"),
                                         (503, "Database unavailable")])
def test_game_access_errors_are_preserved(audio_client, monkeypatch, status, detail):
    client, _ = audio_client
    def unavailable(game_id, student_id):
        raise HTTPException(status_code=status, detail=detail)
    monkeypatch.setattr(game_session, "current_location", unavailable)
    response = client.get(URL)
    assert response.status_code == status
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_non_students_cannot_play_audio(audio_client, role):
    client, user = audio_client
    user["role"] = role
    assert client.get(URL).status_code == 403


def test_audio_requires_login(audio_client):
    client, _ = audio_client
    app.dependency_overrides.clear()
    assert client.get(URL).status_code == 401
