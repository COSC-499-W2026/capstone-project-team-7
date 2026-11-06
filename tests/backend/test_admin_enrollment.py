import os
from hashlib import sha256
from uuid import uuid4

import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin
import admin_enrollment
import auth
from database import get_connection

app = FastAPI()
app.include_router(admin.router)
app.include_router(admin_enrollment.router)
client = TestClient(app)


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
        self.queries.append(query)
        if query.startswith("INSERT") and self.rows and isinstance(self.rows[0], Exception):
            raise self.rows.pop(0)
        return self

    def fetchone(self):
        return self.rows.pop(0)


def use_connection(monkeypatch, connection):
    monkeypatch.setattr(auth, "get_connection", connection)
    monkeypatch.setattr(admin_enrollment, "get_connection", connection)


def enroll(info=None, class_id=None, token="admin-token"):
    client.cookies.set("session", token)
    return client.post(f"/api/admin/classes/{class_id or uuid4()}/students", json=info or {"student_number": "12345678"})


def enrolled(connection):
    return any(query.startswith("INSERT") for query in connection.queries)


def test_admin_enrolls_student_in_any_class(monkeypatch):
    class_id, student_id = uuid4(), uuid4()
    # Rows: admin session, class, student.
    connection = FakeConnection({"role": "admin"}, {"id": class_id}, {"user_id": student_id, "student_number": "12345678"})
    use_connection(monkeypatch, connection)

    response = enroll({"student_number": " 12345678 "}, class_id)

    assert response.status_code == 201
    assert response.json() == {"class_id": str(class_id), "student_id": str(student_id), "student_number": "12345678"}
    assert enrolled(connection)


def test_unknown_class_returns_404(monkeypatch):
    connection = FakeConnection({"role": "admin"}, None)
    use_connection(monkeypatch, connection)

    response = enroll()

    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}
    assert not enrolled(connection)


def test_unknown_student_returns_404(monkeypatch):
    connection = FakeConnection({"role": "admin"}, {"id": uuid4()}, None)
    use_connection(monkeypatch, connection)

    response = enroll()

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}
    assert not enrolled(connection)


def test_already_enrolled_returns_409(monkeypatch):
    student = {"user_id": uuid4(), "student_number": "12345678"}
    connection = FakeConnection({"role": "admin"}, {"id": uuid4()}, student, psycopg.errors.UniqueViolation())
    use_connection(monkeypatch, connection)

    response = enroll()

    assert response.status_code == 409
    assert response.json() == {"detail": "Student already enrolled"}


@pytest.mark.parametrize("info", [
    {"student_number": " "},
    {"student_number": "1" * 31},
    {"student_number": "12345678", "role": "admin"},
    {},
], ids=["blank", "too-long", "extra-field", "missing"])
def test_invalid_details_return_422(monkeypatch, info):
    connection = FakeConnection({"role": "admin"})
    use_connection(monkeypatch, connection)

    client.cookies.set("session", "admin-token")
    assert client.post(f"/api/admin/classes/{uuid4()}/students", json=info).status_code == 422
    assert not enrolled(connection)


def test_invalid_class_id_returns_422(monkeypatch):
    use_connection(monkeypatch, FakeConnection({"role": "admin"}))

    assert enroll(class_id="not-a-uuid").status_code == 422


@pytest.mark.parametrize("session,status", [(None, 401), ({"role": "teacher"}, 403), ({"role": "student"}, 403)])
def test_only_logged_in_admins_can_enroll(monkeypatch, session, status):
    connection = FakeConnection(session)
    use_connection(monkeypatch, connection)

    assert enroll().status_code == status
    assert not enrolled(connection)


def test_database_failure_returns_503(monkeypatch):
    def unavailable():
        raise RuntimeError("DATABASE_URL is missing")

    monkeypatch.setattr(auth, "get_connection", FakeConnection({"role": "admin"}))
    monkeypatch.setattr(admin_enrollment, "get_connection", unavailable)

    assert enroll().status_code == 503


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_admin_enrolls_student_in_another_teachers_class():
    def user(role):
        return connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, 'test-only-encoded-hash', 'Test', 'User', %s) RETURNING id
        ''', (uuid4().hex + "@example.com", uuid4().hex, role)).fetchone()["id"]

    student_number = uuid4().hex[:20]
    with get_connection() as connection:
        admin_id, teacher_id, student_id = user("admin"), user("teacher"), user("student")
        connection.execute("INSERT INTO teachers (user_id) VALUES (%s)", (teacher_id,))
        connection.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (student_id, student_number))
        class_id = connection.execute(
            "INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'French 101', 'fr') RETURNING id",
            (teacher_id,),
        ).fetchone()["id"]
        token = uuid4().hex
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 hour')",
            (sha256(token.encode()).hexdigest(), admin_id),
        )

    try:
        assert enroll({"student_number": student_number}, class_id, token).status_code == 201
        assert enroll({"student_number": student_number}, class_id, token).status_code == 409
        with get_connection() as connection:
            assert connection.execute(
                "SELECT student_id FROM class_enrollments WHERE class_id = %s", (class_id,)
            ).fetchall() == [{"student_id": student_id}]
    finally:
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = ANY(%s)", ([admin_id, teacher_id, student_id],))
