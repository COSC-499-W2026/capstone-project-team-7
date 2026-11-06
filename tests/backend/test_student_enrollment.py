import os
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

import auth
import student_enrollment
from database import get_connection
from main import app
from migrate import apply_migrations
from utils.passwords import hash_password

URL = "/api/student/classes/join"
PASSWORD = "test-password"
CODE = "ABC123DEF456"


@pytest.fixture
def enrollment_db(monkeypatch):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run student enrollment integration tests")
    schema = "enrollment_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            connection.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            apply_migrations(connection)
            monkeypatch.setenv("DATABASE_URL", make_conninfo(url, options=f"-c search_path={schema}"))
            with get_connection() as db:
                users = {}
                for role in ("student", "teacher", "admin"):
                    users[role] = db.execute("""INSERT INTO users
                        (email, username, password, first_name, last_name, role)
                        VALUES (%s, %s, %s, 'Test', 'User', %s) RETURNING id""",
                        (role + "@example.com", role, hash_password(PASSWORD), role)).fetchone()["id"]
                db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '12345678')",
                           (users["student"],))
                db.execute("INSERT INTO teachers (user_id) VALUES (%s)", (users["teacher"],))
                class_id = db.execute("""INSERT INTO classes (teacher_id, name, language_code, class_code)
                    VALUES (%s, 'French 101', 'fr', %s) RETURNING id""",
                    (users["teacher"], CODE)).fetchone()["id"]
            yield str(class_id)
        finally:
            connection.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def client():
    # HTTPS allows TestClient to send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client


def login(client, role="student"):
    response = client.post("/api/auth/login", json={"email": role + "@example.com", "password": PASSWORD})
    assert response.status_code == 200, response.text


def enrollment_count():
    with get_connection() as db:
        return db.execute("SELECT count(*) AS n FROM class_enrollments").fetchone()["n"]


@pytest.mark.parametrize("code", [CODE, "  abc123def456  "])
def test_student_joins_class_with_code(enrollment_db, client, code):
    login(client)
    response = client.post(URL, json={"class_code": code})
    assert response.status_code == 201
    assert response.json() == {"id": enrollment_db, "name": "French 101", "language_code": "fr"}
    with get_connection() as db:
        enrollment = db.execute("""SELECT e.class_id FROM class_enrollments e
            JOIN users u ON u.id = e.student_id WHERE u.email = 'student@example.com'""").fetchone()
    assert str(enrollment["class_id"]) == enrollment_db


def test_unknown_code_returns_not_found(enrollment_db, client):
    login(client)
    response = client.post(URL, json={"class_code": "ZZZZZZZZZZZZ"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}
    assert enrollment_count() == 0


def test_joining_twice_returns_conflict(enrollment_db, client):
    login(client)
    assert client.post(URL, json={"class_code": CODE}).status_code == 201
    response = client.post(URL, json={"class_code": CODE})
    assert response.status_code == 409
    assert response.json() == {"detail": "Already enrolled"}
    assert enrollment_count() == 1


@pytest.mark.parametrize("body", [{}, {"class_code": "   "}, {"class_code": CODE + "X"},
                                  {"class_code": 123}, {"class_code": CODE, "extra": 1}])
def test_join_rejects_bad_input(enrollment_db, client, body):
    login(client)
    assert client.post(URL, json=body).status_code == 422
    assert enrollment_count() == 0


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_join_requires_student(enrollment_db, client, role, status):
    if role:
        login(client, role)
    assert client.post(URL, json={"class_code": CODE}).status_code == status
    assert enrollment_count() == 0


def test_expired_session_is_rejected(enrollment_db, client):
    login(client)
    with get_connection() as db:
        db.execute("UPDATE sessions SET expires_at = now() - interval '1 second'")
    assert client.post(URL, json={"class_code": CODE}).status_code == 401
    assert enrollment_count() == 0


def test_session_check_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(auth, "get_connection", unavailable)
    client.cookies.set("session", "test-token")
    response = client.post(URL, json={"class_code": CODE})
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_join_database_failure_is_safe(client, monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    app.dependency_overrides[student_enrollment.require_student] = lambda: {"id": uuid4(), "role": "student"}
    monkeypatch.setattr(student_enrollment, "get_connection", unavailable)
    try:
        response = client.post(URL, json={"class_code": CODE})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
