from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import auth
import student_badges
from badges import BADGES
from main import app
from test_auth import FakeConnection
from test_game_session import URL as START_URL, add_locations, answer, game_db, login

URL = "/api/student/badges"
USER = {"id": uuid4(), "role": "student"}
EARNED_AT = datetime(2026, 10, 28, tzinfo=timezone.utc)


def fake_badges(monkeypatch, rows):
    """Pretend the student_badges table holds these rows for the student."""
    class Connection(FakeConnection):
        def __init__(self):
            pass
        def execute(self, query, params):
            assert params == (USER["id"],)
            return self
        def fetchall(self):
            return rows
    monkeypatch.setattr(student_badges, "get_connection", Connection)


@pytest.fixture
def client():
    # HTTPS allows TestClient to send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


def test_earned_badges_are_marked_and_the_rest_locked(client, monkeypatch):
    app.dependency_overrides[auth.current_user] = lambda: USER
    fake_badges(monkeypatch, [{"badge_id": "fr_first_hunt", "earned_at": EARNED_AT},
                              {"badge_id": "fr_basic", "earned_at": EARNED_AT}])

    badges = {badge["id"]: badge for badge in client.get(URL).json()}

    assert len(badges) == len(BADGES)
    assert badges["fr_basic"] == {"id": "fr_basic", "name": "French Basic", "language": "fr",
                                  "earned": True, "earned_at": EARNED_AT.isoformat()}
    assert badges["fr_first_hunt"]["earned"] is True
    locked = [badge for id, badge in badges.items() if id not in ("fr_basic", "fr_first_hunt")]
    assert all(not badge["earned"] and badge["earned_at"] is None for badge in locked)


def test_new_student_gets_every_badge_locked(client, monkeypatch):
    app.dependency_overrides[auth.current_user] = lambda: USER
    fake_badges(monkeypatch, [])

    response = client.get(URL)

    assert response.status_code == 200
    assert len(response.json()) == len(BADGES)
    assert all(not badge["earned"] and badge["earned_at"] is None for badge in response.json())


def test_not_logged_in_is_unauthorized(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_teachers_and_admins_are_forbidden(client, role):
    app.dependency_overrides[auth.current_user] = lambda: dict(USER, role=role)
    assert client.get(URL).status_code == 403


def earned(client):
    return {badge["id"] for badge in client.get(URL).json() if badge["earned"]}


def test_finding_the_last_basic_french_location_awards_french_basic(game_db, client):
    add_locations(5, "fr")
    login(client)
    game_id = client.post(START_URL).json()["game_id"]
    for _ in range(4):
        answer(client, game_id)
    assert "fr_basic" not in earned(client)

    answer(client, game_id)

    assert "fr_basic" in earned(client)


def test_finishing_a_first_french_game_awards_french_first_hunt(game_db, client):
    # One more location than a game uses, so finishing the game can't also earn French Basic.
    add_locations(6, "fr")
    login(client)
    game_id = client.post(START_URL).json()["game_id"]
    for _ in range(4):
        answer(client, game_id)
    assert earned(client) == set()

    answer(client, game_id)

    assert earned(client) == {"fr_first_hunt"}
