import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

import teacher_access
from database import get_connection
from main import app
from migrate import apply_migrations
from utils.passwords import hash_password

URL = "/api/teacher/classes"
PASSWORD = "test-password"


@pytest.fixture
def access_db(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run class access integration tests")
    schema = "access_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                for role in ("teacher", "teacher2", "student", "admin"):
                    user = db.execute("""INSERT INTO users
                        (email, username, password, first_name, last_name, role)
                        VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
                        (role + "@example.com", role, hash_password(PASSWORD),
                         "teacher" if role == "teacher2" else role)).fetchone()["id"]
                    if role.startswith("teacher"):
                        db.execute("INSERT INTO teachers (user_id) VALUES (%s)", (user,))
                        classroom = db.execute("""INSERT INTO classes (teacher_id, name, language_code)
                            VALUES (%s, %s, 'fr') RETURNING id""", (user, role)).fetchone()["id"]
                        if role == "teacher":
                            own_class = str(classroom)
            yield own_class
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    # HTTPS allows TestClient to send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def login(client, role="teacher"):
    response = client.post("/api/auth/login", json={"email": role + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


def test_teacher_lists_only_assigned_classes(access_db, client):
    login(client)
    response = client.get(URL)
    assert response.status_code == 200
    assert len(response.json()) == 1
    classroom = response.json()[0]
    assert classroom == {"id": access_db, "name": "teacher", "language_code": "fr",
                         "class_code": classroom["class_code"]}
    assert len(classroom["class_code"]) == 12


def test_teacher_reads_assigned_class(access_db, client):
    login(client)
    response = client.get(URL + "/" + access_db)
    assert response.status_code == 200
    assert response.json() == client.get(URL).json()[0]


def test_teacher_without_classes_gets_empty_list(access_db, client):
    login(client)
    with get_connection() as db:
        db.execute("DELETE FROM classes WHERE id = %s", (access_db,))
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("suffix", ["", "/00000000-0000-0000-0000-000000000000"])
@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_requires_teacher_session(access_db, client, suffix, role, status):
    if role:
        login(client, role)
    assert client.get(URL + suffix).status_code == status


def test_other_teacher_and_missing_class_are_hidden(access_db, client):
    login(client, "teacher2")
    for class_id in (access_db, str(uuid4())):
        response = client.get(URL + "/" + class_id)
        assert response.status_code == 404
        assert response.json() == {"detail": "Class not found"}


@pytest.mark.parametrize("expired", [False, True])
def test_invalid_or_expired_session(access_db, client, expired):
    login(client)
    with get_connection() as db:
        db.execute("UPDATE sessions SET expires_at = now() - interval '1 second'" if expired else "DELETE FROM sessions")
    assert client.get(URL).status_code == 401


def test_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(teacher_access, "get_connection", unavailable)
    client.cookies.set("session", "test-token")
    response = client.get(URL)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
