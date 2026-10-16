from hashlib import sha256
from datetime import timedelta
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import teacher_approval
from database import get_connection
from main import app
from test_teacher_signup import signup_database
from utils.passwords import hash_password

URL = "/api/admin/approved-teachers"


@pytest.fixture
def client():
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def session(client, role="admin", expired=False):
    with get_connection() as db:
        user = db.execute(
            """INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
            (uuid4().hex + "@example.com", uuid4().hex, hash_password("password123"), role),
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + %s)",
            (sha256(b"test-token").hexdigest(), user,
             timedelta(days=-1 if expired else 1)),
        )
    client.cookies.set("session", "test-token")


def test_admin_approval_enables_signup(signup_database, client):
    session(client)
    response = client.post(URL, json={"email": " Teacher@Example.com "})
    assert response.status_code == 201
    assert response.json() == {"email": "teacher@example.com", "approved": True}
    with get_connection() as db:
        assert db.execute("SELECT email FROM authorized_teacher_emails").fetchall() == [
            {"email": "teacher@example.com"}]
    assert client.post("/api/auth/teacher/signup", json={
        "email": "teacher@example.com", "username": "teacher", "password": "password123",
        "first_name": "Test", "last_name": "Teacher",
    }).status_code == 201
    assert client.post(URL, json={"email": "TEACHER@example.com"}).status_code == 409


@pytest.mark.parametrize("role,expired,status", [
    ("teacher", False, 403), ("student", False, 403),
    (None, False, 401), ("admin", True, 401),
])
def test_rejected_requests_do_not_approve(signup_database, client, role, expired, status):
    if role:
        session(client, role, expired)
    else:
        client.cookies.set("session", "unknown-token")
    assert client.post(URL, json={"email": "teacher@example.com"}).status_code == status
    with get_connection() as db:
        assert db.execute("SELECT count(*) AS n FROM authorized_teacher_emails").fetchone()["n"] == 0


def test_missing_session_does_not_open_database(monkeypatch, client):
    def unexpected():
        pytest.fail("Missing cookie should not open a connection")
    monkeypatch.setattr(teacher_approval, "get_connection", unexpected)
    assert client.post(URL, json={"email": "teacher@example.com"}).status_code == 401


@pytest.mark.parametrize("body", [{}, {"email": "bad"}, {"email": " "},
                                       {"email": "a@b.com", "role": "admin"}])
def test_invalid_body_does_not_open_database(monkeypatch, client, body):
    def unexpected():
        pytest.fail("Invalid input should not open a connection")
    monkeypatch.setattr(teacher_approval, "get_connection", unexpected)
    assert client.post(URL, json=body).status_code == 422


def test_database_failure_is_safe(monkeypatch, client):
    def unavailable():
        raise psycopg.OperationalError("private connection details")
    monkeypatch.setattr(teacher_approval, "get_connection", unavailable)
    client.cookies.set("session", "test-token")
    response = client.post(URL, json={"email": "teacher@example.com"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
