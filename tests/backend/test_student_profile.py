from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import student_profile
from database import get_connection
from main import app
from test_auth import FakeConnection
from test_student_enrollment import enrollment_db, login

URL = "/api/student/profile"
USER = {"id": uuid4(), "role": "student"}


@pytest.fixture
def client(monkeypatch):
    app.dependency_overrides[auth.current_user] = lambda: USER
    class Connection(FakeConnection):
        def __init__(self):
            self.results = [{"username": "learner"}, [], []]
        def execute(self, query, params):
            assert all(value == USER["id"] for value in params)
            return self
        def fetchone(self):
            return self.results.pop(0)
        def fetchall(self):
            return self.results.pop(0)
    monkeypatch.setattr(student_profile, "get_connection", Connection)
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


def test_empty_profile_and_own_id(client):
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == client.get(URL + "/" + str(USER["id"])).json()
    assert response.json()["username"] == "learner"
    assert response.json()["profile_icon"] is None
    assert response.json()["classes"] == response.json()["languages"] == []


def test_other_students_profile_is_forbidden(client):
    response = client.get(URL + "/" + str(uuid4()))
    assert response.status_code == 403
    assert response.json() == {"detail": "You can only access your own profile"}


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_non_students_are_forbidden(client, role):
    app.dependency_overrides[auth.current_user] = lambda: dict(USER, role=role)
    assert client.get(URL).status_code == 403


def test_missing_and_invalid_sessions(client, monkeypatch):
    app.dependency_overrides.clear()
    assert client.get(URL).status_code == 401
    monkeypatch.setattr(auth, "get_connection", FakeConnection(None))
    client.cookies.set("session", "invalid")
    assert client.get(URL).status_code == 401


def test_invalid_id(client):
    assert client.get(URL + "/invalid").status_code == 422


def test_missing_student_record(client, monkeypatch):
    monkeypatch.setattr(student_profile, "get_connection", FakeConnection(None))
    response = client.get(URL)
    assert response.status_code == 404
    assert response.json() == {"detail": "Student profile not found"}


@pytest.mark.parametrize("error", [RuntimeError("private details"), psycopg.OperationalError("secret")])
def test_database_failure_is_safe(client, monkeypatch, error):
    def unavailable():
        raise error
    monkeypatch.setattr(student_profile, "get_connection", unavailable)
    response = client.get(URL)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_profile_with_classes_and_distinct_languages(enrollment_db):
    with get_connection() as db:
        student = db.execute("SELECT id FROM users WHERE username = 'student'").fetchone()["id"]
        db.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)",
                   (enrollment_db, student))
        for code in ("fr", "ja"):
            db.execute("INSERT INTO student_languages VALUES (%s, %s)", (student, code))
        other = db.execute("""INSERT INTO users
            (email, username, password, first_name, last_name, role)
            VALUES ('other@example.com', 'other', 'hash', 'Other', 'User', 'student') RETURNING id""").fetchone()["id"]
        db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '99999999')", (other,))
        db.execute("INSERT INTO student_languages VALUES (%s, 'es')", (other,))
    with TestClient(app, base_url="https://testserver") as client:
        login(client)
        response = client.get(URL)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "student"
    assert data["profile_icon"] is None
    assert data["classes"] == [{"id": enrollment_db, "name": "French 101", "language_code": "fr"}]
    assert data["languages"] == [{"code": "fr", "name": "French"}, {"code": "ja", "name": "Japanese"}]
    assert not {"password", "student_number", "email"} & data.keys()
