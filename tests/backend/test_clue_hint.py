from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import game_session
import proximity
from main import app


@pytest.fixture
def hint_client(monkeypatch):
    game_id = uuid4()
    location = {
        "current_position": 1, "revision": 0, "clue_elapsed_seconds": 300,
        "latitude": 49.94, "longitude": -119.4,
    }
    monkeypatch.setattr(game_session, "current_location", lambda *_: location)
    app.dependency_overrides[game_session.require_student] = lambda: {"id": uuid4()}
    with TestClient(app) as client:
        yield client, game_id, location
    app.dependency_overrides.clear()


def get_hint(client, game_id, **overrides):
    params = {"position": 1, "revision": 0, "latitude": 49.94, "longitude": -119.4,
              "accuracy": 5, "captured_at": datetime.now(timezone.utc).isoformat(), **overrides}
    return client.get(f"/api/game/{game_id}/clue/hint", params=params)


@pytest.mark.parametrize("distance,message", [(0, "You are getting close"), (10, "You are getting close"),
                                               (10.01, "You are too far")])
def test_hint_distance_boundary(hint_client, monkeypatch, distance, message):
    client, game_id, _ = hint_client
    monkeypatch.setattr(proximity, "distance_metres", lambda *_: distance)
    response = get_hint(client, game_id)
    assert response.status_code == 200
    assert response.json() == {"message": message}


def test_hint_not_available_before_five_minutes(hint_client):
    client, game_id, location = hint_client
    location["clue_elapsed_seconds"] = 299
    assert get_hint(client, game_id).status_code == 409


@pytest.mark.parametrize("overrides", [
    {"accuracy": 10.01},
    {"captured_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()},
    {"latitude": 91},
])
def test_hint_rejects_unreliable_or_invalid_location(hint_client, overrides):
    client, game_id, _ = hint_client
    assert get_hint(client, game_id, **overrides).status_code == 422


def test_hint_rejects_outdated_clue(hint_client):
    client, game_id, _ = hint_client
    assert get_hint(client, game_id, revision=1).status_code == 409


def test_hint_handles_missing_target(hint_client):
    client, game_id, location = hint_client
    location["latitude"] = None
    assert get_hint(client, game_id).status_code == 503


def test_hint_requires_login():
    with TestClient(app) as client:
        assert get_hint(client, uuid4()).status_code == 401
