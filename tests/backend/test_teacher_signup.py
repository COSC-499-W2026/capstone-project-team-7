import os
from uuid import UUID, uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
import pytest
from fastapi.testclient import TestClient

import teacher_signup
from main import app
from migrate import apply_migrations
from utils.passwords import verify_password

client = TestClient(app)
INFO = dict(email="teacher@example.com", username="teacher", password="password123",
            first_name="Test", last_name="Teacher")
URL = "/api/auth/teacher/signup"


@pytest.fixture
def signup_database(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run teacher signup integration tests")
    schema = "signup_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True, connect_timeout=5) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            # The endpoint uses its real connection helper and commits normally.
            isolated_url = make_conninfo(url, options=f"-c search_path={schema}")
            monkeypatch.setenv("DATABASE_URL", isolated_url)
            yield isolated_url
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.mark.parametrize("changes", [
    {},
    {"email": " Teacher@Example.com "},
    {"username": " teacher ", "first_name": " Test ", "last_name": " Teacher "},
    {"password": "é" * 36},
], ids=["standard", "normalized-email", "trimmed-details", "72-byte-password"])
def test_authorized_teacher_signup_persists_account(signup_database, changes):
    info = {**INFO, **changes}
    with psycopg.connect(signup_database) as connection:
        connection.execute(
            "INSERT INTO authorized_teacher_emails (email) VALUES (%s)", (INFO["email"],)
        )

    response = client.post(URL, json=info)
    assert response.status_code == 201, response.text
    user_id = UUID(response.json()["id"])
    assert response.json() == {"id": str(user_id), "role": "teacher"}

    # A separate connection proves both records were committed by the request.
    with psycopg.connect(signup_database, row_factory=dict_row) as connection:
        user = connection.execute("SELECT * FROM users WHERE id = %s", (user_id,)).fetchone()
        teacher = connection.execute(
            "SELECT user_id, role FROM teachers WHERE user_id = %s", (user_id,)
        ).fetchone()
    assert user is not None
    for field in ("email", "username", "first_name", "last_name"):
        assert user[field] == INFO[field]
    assert user["role"] == "teacher"
    assert user["password"] != info["password"]
    assert verify_password(info["password"], user["password"])
    assert teacher == {"user_id": user_id, "role": "teacher"}


def test_unauthorized_signup_creates_no_account(signup_database):
    response = client.post(URL, json=INFO)
    assert response.status_code == 403
    assert response.json() == {"detail": "Error, unauthorized account"}
    with psycopg.connect(signup_database) as connection:
        assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM teachers").fetchone()[0] == 0


def test_duplicate_signup_returns_conflict(signup_database):
    with psycopg.connect(signup_database) as connection:
        connection.execute(
            "INSERT INTO authorized_teacher_emails (email) VALUES (%s)", (INFO["email"],)
        )
    assert client.post(URL, json=INFO).status_code == 201
    response = client.post(URL, json=INFO)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email or username already in use"}
    with psycopg.connect(signup_database) as connection:
        assert connection.execute("SELECT count(*) FROM users").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM teachers").fetchone()[0] == 1


@pytest.mark.parametrize("changes", [
    {"email": "invalid"}, {"username": " "}, {"password": "short"},
    {"password": "é" * 37}, {"role": "admin"},
])
def test_invalid_signup_does_not_open_database(monkeypatch, changes):
    def unexpected_connection():
        pytest.fail("Invalid signup should not reach the database")

    monkeypatch.setattr(teacher_signup, "get_connection", unexpected_connection)
    assert client.post(URL, json={**INFO, **changes}).status_code == 422


def test_database_failure_returns_safe_error(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private connection details")

    monkeypatch.setattr(teacher_signup, "get_connection", unavailable)
    response = client.post(URL, json=INFO)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
