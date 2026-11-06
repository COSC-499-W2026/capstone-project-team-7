from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import game_session
from main import app
from test_auth import FakeConnection


@pytest.fixture
def client():
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4(), "role": "student"}
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.parametrize("language", ["zh", "fr", "de", "ja", "ko", "es"])
@pytest.mark.parametrize("difficulty", ["basic", "advanced", "expert"])
def test_choices_select_pool_and_are_saved(client, monkeypatch, language, difficulty):
    calls = []
    ids = [uuid4() for _ in range(5)]
    class Connection(FakeConnection):
        def execute(self, query, params):
            calls.append((query, params))
            return self

        def fetchall(self):
            return [{"location_id": id} for id in ids]

        def fetchone(self):
            return {"id": uuid4(), "language_code": language, "difficulty": difficulty, "current_position": 1}

    monkeypatch.setattr(game_session, "get_connection", Connection(None))
    response = client.post('/api/game/start', json={"language_code": language, "difficulty": difficulty})
    assert response.status_code == 201
    assert response.json()["difficulty"] == difficulty
    assert response.json()["language_code"] == language
    assert calls[0][1] == (language,)
    assert calls[1][1][1:] == (language, difficulty)
    assert {params[2] for _, params in calls[2:]} == set(ids)


@pytest.mark.parametrize("body", [{"language_code": "xx"}, {"difficulty": "easy"},
                                  {"language_code": None}, {"difficulty": None}, {"points": 100}])
def test_invalid_choices_never_reach_database(client, monkeypatch, body):
    def unexpected():
        raise AssertionError('Invalid input should not reach the database')
    monkeypatch.setattr(game_session, "get_connection", unexpected)
    assert client.post('/api/game/start', json=body).status_code == 422
