"""Debrief data comes only from the signed-in student's completed hunts."""

from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient

import student_debrief
from database import get_connection
from main import app
from test_student_progress import add_game, client, login, users  # shared isolated Postgres fixtures

URL = "/api/student/debrief"


def test_completed_hunts_summarize_listens_and_attempts(users, client):
    add_game(users["student"], "2026-11-01", spots=[("A", 3, 1), ("B", 0, 3), ("C", 1, 1)])
    add_game(users["student"], "2026-11-02", spots=[("D", 2, 1)])
    add_game(users["student"], None, spots=[("UNFINISHED", 20, 20)])
    add_game(users["other"], "2026-11-03", spots=[("OTHER", 20, 20)])
    with get_connection() as db:
        location = db.execute("SELECT id FROM locations WHERE building = 'B'").fetchone()["id"]
        db.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
            VALUES (%s, 'fr', 'cent un', 'près de la porte'), (%s, 'es', 'ciento uno', 'cerca')""",
            (location, location))
    login(client)
    response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert body["completed_hunts"] == 2
    assert [item["building"] for item in body["difficulties"]] == ["B", "A", "D"]
    assert body["difficulties"][0] == {
        "building": "B", "room_number": "101", "language_code": "fr", "difficulty": "basic",
        "hunts": 1, "listens": 0, "attempts": 3, "extra_attempts": 2,
        "number_text": "cent un", "description_text": "près de la porte",
    }


def test_debrief_aggregates_same_location_across_hunts(users, client):
    add_game(users["student"], "2026-11-01", spots=[("A", 3, 2)])
    with get_connection() as db:
        location = db.execute("SELECT id FROM locations WHERE building = 'A'").fetchone()["id"]
        game = db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, finished_at)
            VALUES (%s, 'fr', 'basic', now()) RETURNING id""", (users["student"],)).fetchone()["id"]
        db.execute("""INSERT INTO game_session_locations (game_session_id, position, location_id, listens, attempts)
            VALUES (%s, 1, %s, 1, 3)""", (game, location))
    login(client)
    data = client.get(URL).json()
    assert data["completed_hunts"] == 2
    assert data["difficulties"] == [{"building": "A", "room_number": "101", "language_code": "fr",
                                     "difficulty": "basic", "hunts": 2, "listens": 4,
                                     "attempts": 5, "extra_attempts": 3, "number_text": None, "description_text": None}]


def test_no_completed_hunts_returns_empty_summary(users, client):
    add_game(users["student"], None, spots=[("A", 5, 5)])
    add_game(users["other"], "2026-11-01", spots=[("B", 5, 5)])
    login(client)
    assert client.get(URL).json() == {"completed_hunts": 0, "difficulties": []}


def test_debrief_requires_student(users, client):
    assert client.get(URL).status_code == 401
    login(client, "teacher")
    assert client.get(URL).status_code == 403


def test_database_failure_is_safe(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(student_debrief, "get_connection", unavailable)
    app.dependency_overrides[student_debrief.require_student] = lambda: {"id": uuid4()}
    try:
        with TestClient(app) as client:
            response = client.get(URL)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_endpoint_returns_debrief_and_uses_student_id(monkeypatch):
    student_id = uuid4()
    difficulty = {"building": "A", "room_number": "101", "language_code": "fr", "difficulty": "basic",
                  "hunts": 1, "listens": 2, "attempts": 1, "extra_attempts": 0}
    calls = []

    class Result:
        def fetchone(self):
            return {"completed_hunts": 1}

        def fetchall(self):
            return [difficulty]

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def execute(self, query, params):
            calls.append((query, params))
            return Result()

    monkeypatch.setattr(student_debrief, "get_connection", Connection)
    app.dependency_overrides[student_debrief.require_student] = lambda: {"id": student_id}
    try:
        with TestClient(app) as client:
            response = client.get(URL)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"completed_hunts": 1, "difficulties": [difficulty]}
    assert len(calls) == 2
    assert all(params == (student_id,) for _, params in calls)


def test_endpoint_requires_login():
    with TestClient(app) as client:
        assert client.get(URL).status_code == 401
