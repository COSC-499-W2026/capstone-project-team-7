import os
from hashlib import sha256
from uuid import uuid4

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin
import admin_creation
import auth
from database import get_connection
from utils.passwords import verify_password

app = FastAPI()
app.include_router(admin.router)
app.include_router(admin_creation.router)
app.include_router(auth.router)
client = TestClient(app)

INFO = dict(email="new.admin@example.com", username="newadmin", password="password123",
            first_name="New", last_name="Admin")


class FakeConnection:
    """Stands in for get_connection(); answers each fetchone() with the next queued row, raising queued errors."""

    def __init__(self, *rows):
        self.rows = list(rows)
        self.queries = []

    def __call__(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query, params):
        self.queries.append((query, params))
        if isinstance(self.rows[0], Exception):
            raise self.rows.pop(0)
        return self

    def fetchone(self):
        return self.rows.pop(0)


def use_connection(monkeypatch, connection):
    monkeypatch.setattr(auth, "get_connection", connection)
    monkeypatch.setattr(admin_creation, "get_connection", connection)


def create_admin(info=None, token="admin-token"):
    client.cookies.set("session", token)
    return client.post("/api/admin/admins", json=info or INFO)


def inserted(connection):
    return [params for query, params in connection.queries if query.startswith("INSERT")]


def test_admin_creates_admin_with_hashed_password(monkeypatch):
    user_id = uuid4()
    created = {"id": user_id, "email": INFO["email"], "username": INFO["username"], "role": "admin"}
    connection = FakeConnection({"role": "admin"}, created)
    use_connection(monkeypatch, connection)

    response = create_admin({**INFO, "email": " New.Admin@Example.com "})

    assert response.status_code == 201
    assert response.json() == {**created, "id": str(user_id)}
    (params,) = inserted(connection)
    assert params[0] == INFO["email"]
    assert INFO["password"] not in params
    assert verify_password(INFO["password"], params[2])


def test_duplicate_email_or_username_returns_409(monkeypatch):
    connection = FakeConnection({"role": "admin"}, psycopg.errors.UniqueViolation())
    use_connection(monkeypatch, connection)

    response = create_admin()

    assert response.status_code == 409
    assert response.json() == {"detail": "Email or username already in use"}


@pytest.mark.parametrize("changes", [
    {"email": "not-an-email"},
    {"password": "short"},
    {"password": "é" * 37},
    {"username": " "},
    {"role": "student"},
], ids=["bad-email", "short-password", "long-password", "blank-username", "extra-field"])
def test_invalid_details_return_422(monkeypatch, changes):
    connection = FakeConnection({"role": "admin"})
    use_connection(monkeypatch, connection)

    assert create_admin({**INFO, **changes}).status_code == 422
    assert not inserted(connection)


@pytest.mark.parametrize("session,status", [(None, 401), ({"role": "teacher"}, 403), ({"role": "student"}, 403)])
def test_only_logged_in_admins_can_create_admins(monkeypatch, session, status):
    connection = FakeConnection(session)
    use_connection(monkeypatch, connection)

    assert create_admin().status_code == status
    assert not inserted(connection)


def test_database_failure_returns_503(monkeypatch):
    def unavailable():
        raise RuntimeError("DATABASE_URL is missing")

    monkeypatch.setattr(auth, "get_connection", FakeConnection({"role": "admin"}))
    monkeypatch.setattr(admin_creation, "get_connection", unavailable)

    assert create_admin().status_code == 503


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_new_admin_can_log_in():
    email, username = uuid4().hex + "@example.com", uuid4().hex
    with get_connection() as connection:
        admin_id = connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, 'test-only-encoded-hash', 'Test', 'Admin', 'admin') RETURNING id
        ''', (uuid4().hex + "@example.com", uuid4().hex)).fetchone()["id"]
        token = uuid4().hex
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 hour')",
            (sha256(token.encode()).hexdigest(), admin_id),
        )

    try:
        response = create_admin({**INFO, "email": email, "username": username}, token)
        assert response.status_code == 201
        assert response.json()["role"] == "admin"
        assert create_admin({**INFO, "email": email, "username": uuid4().hex}, token).status_code == 409

        client.cookies.clear()
        login = client.post("/api/auth/login", json={"email": email, "password": INFO["password"]})
        assert login.status_code == 200
        assert login.json()["role"] == "admin"
    finally:
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = %s OR lower(email) = %s", (admin_id, email))
