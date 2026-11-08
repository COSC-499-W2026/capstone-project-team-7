from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import student_leaderboard
from database import get_connection
from main import app
from test_auth import FakeConnection
from test_student_enrollment import enrollment_db, login

CLASS_ID = uuid4()
URL = f"/api/student/classes/{CLASS_ID}/leaderboard"
USER = {"id": uuid4(), "role": "student"}


@pytest.fixture
def client():
    app.dependency_overrides[auth.current_user] = lambda: USER
    try:
        with TestClient(app, base_url="https://testserver") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("role,status", [("teacher", 403), ("admin", 403), (None, 401)])
def test_requires_student(client, role, status):
    if role:
        app.dependency_overrides[auth.current_user] = lambda: {**USER, "role": role}
    else:
        app.dependency_overrides.clear()
    assert client.get(URL).status_code == status


def test_invalid_session(client, monkeypatch):
    app.dependency_overrides.clear()
    monkeypatch.setattr(auth, "get_connection", FakeConnection(None))
    client.cookies.set("session", "expired-or-invalid-token")
    assert client.get(URL).status_code == 401


def test_invalid_class_id(client):
    assert client.get("/api/student/classes/invalid/leaderboard").status_code == 422


@pytest.mark.parametrize("missing_class,status", [(True, 404), (False, 403)])
def test_class_access(client, monkeypatch, missing_class, status):
    class Connection(FakeConnection):
        def __init__(self):
            self.rows = [None] if missing_class else [{"language_code": "fr"}, None]
        def fetchone(self):
            return self.rows.pop(0)
    monkeypatch.setattr(student_leaderboard, "get_connection", Connection)
    assert client.get(URL).status_code == status


@pytest.mark.parametrize("error", [psycopg.OperationalError, RuntimeError])
def test_database_failure(client, monkeypatch, error):
    def unavailable():
        raise error("private connection details")
    monkeypatch.setattr(student_leaderboard, "get_connection", unavailable)
    response = client.get(URL)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_rankings_use_completed_language_scores_and_equipped_icons(enrollment_db, client):
    app.dependency_overrides.clear()
    login(client)
    url = f"/api/student/classes/{enrollment_db}/leaderboard"
    assert client.get(URL).status_code == 404
    assert client.get(url).status_code == 403
    with get_connection() as db:
        learner = db.execute("SELECT id FROM users WHERE username = 'student'").fetchone()["id"]
        ids = [learner]
        for name in ("alpha", "zero", "outsider"):
            student = db.execute("""INSERT INTO users
                (email, username, password, first_name, last_name, role)
                VALUES (%s, %s, 'unused', 'Test', 'User', 'student') RETURNING id""",
                (name + "@example.com", name)).fetchone()["id"]
            db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)",
                       (student, name))
            ids.append(student)
        for student in ids[:3]:
            db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)",
                       (enrollment_db, student))
        db.execute("INSERT INTO student_icons (student_id, icon_id) VALUES (%s, 'croissant_cutie')",
                   (learner,))
        db.execute("UPDATE students SET equipped_icon_id = 'croissant_cutie' WHERE user_id = %s",
                   (learner,))
        for student, language, points, finished in [
            (learner, "fr", 100, True), (learner, "fr", 50, True),
            (learner, "fr", 999, False), (learner, "es", 999, True),
            (ids[1], "fr", 150, True), (ids[3], "fr", 1000, True),
        ]:
            db.execute("""INSERT INTO game_sessions
                (student_id, language_code, difficulty, points, finished_at)
                VALUES (%s, %s, 'basic', %s, CASE WHEN %s THEN now() END)""",
                (student, language, points, finished))
    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == [
        {"rank": 1, "username": "alpha", "total_points": 150, "profile_icon": None},
        {"rank": 1, "username": "student", "total_points": 150, "profile_icon": "croissant_cutie"},
        {"rank": 3, "username": "zero", "total_points": 0, "profile_icon": None},
    ]
    with get_connection() as db:
        db.execute("UPDATE sessions SET expires_at = now() - interval '1 second'")
    assert client.get(url).status_code == 401
