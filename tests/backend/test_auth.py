import os
from hashlib import sha256
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
from database import get_connection
from main import app
from utils.passwords import hash_password

client = TestClient(app)

PASSWORD = "correct-password"
HASHED = hash_password(PASSWORD)


class FakeConnection:
    """Stands in for get_connection(); returns `user` for the lookup and records session inserts."""

    def __init__(self, user):
        self.user = user
        self.sessions = []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params):
        if query.startswith("INSERT INTO sessions"):
            self.sessions.append(params)
        return self

    def fetchone(self):
        return self.user


def login(email="user@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


@pytest.mark.parametrize("role", ["student", "teacher", "admin"])
def test_correct_password_creates_session_and_returns_dashboard(monkeypatch, role):
    connection = FakeConnection({"id": uuid4(), "password": HASHED, "role": role})
    monkeypatch.setattr(auth, "get_connection", connection)

    response = login()

    assert response.status_code == 200
    assert response.json() == {"role": role, "redirect_to": auth.DASHBOARDS[role]}
    token = response.cookies[auth.SESSION_COOKIE]
    # Only the hash of the cookie token is stored.
    assert connection.sessions[0][0] == sha256(token.encode()).hexdigest()
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "secure" in cookie


def test_wrong_password_is_rejected_without_session(monkeypatch):
    connection = FakeConnection({"id": uuid4(), "password": HASHED, "role": "student"})
    monkeypatch.setattr(auth, "get_connection", connection)

    response = login(password="wrong-password")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert connection.sessions == []
    assert "set-cookie" not in response.headers


def test_unknown_email_gets_same_error_as_wrong_password(monkeypatch):
    connection = FakeConnection(None)
    monkeypatch.setattr(auth, "get_connection", connection)

    response = login(email="nobody@example.com")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert connection.sessions == []


@pytest.mark.parametrize("body", [{}, {"email": "user@example.com"}, {"password": PASSWORD}])
def test_missing_fields_are_rejected(body):
    assert client.post("/api/auth/login", json=body).status_code == 422


@pytest.mark.parametrize("error", [RuntimeError("missing URL"), psycopg.OperationalError("connection failed")])
def test_database_unavailable_returns_503(monkeypatch, error):
    def unavailable():
        raise error

    monkeypatch.setattr(auth, "get_connection", unavailable)
    response = login()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_login_against_database():
    email = uuid4().hex + "@Example.com"
    with get_connection() as connection:
        user_id = connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, %s, 'Test', 'User', 'teacher') RETURNING id
        ''', (email, uuid4().hex, HASHED)).fetchone()["id"]
    try:
        assert login(email=email.upper(), password="wrong-password").status_code == 401
        response = login(email=email.upper())
        assert response.status_code == 200
        assert response.json()["redirect_to"] == "/teacher/dashboard"
        with get_connection() as connection:
            sessions = connection.execute(
                "SELECT token_hash FROM sessions WHERE user_id = %s", (user_id,)
            ).fetchall()
        token = response.cookies[auth.SESSION_COOKIE]
        assert sessions == [{"token_hash": sha256(token.encode()).hexdigest()}]
    finally:
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s", (user_id,))
