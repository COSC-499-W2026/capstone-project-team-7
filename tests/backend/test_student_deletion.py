import os
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin
import auth
import student_deletion
from database import get_connection

app = FastAPI()
app.include_router(admin.router)
app.include_router(student_deletion.router)
client = TestClient(app)


class FakeConnection:
    """Stands in for get_connection(); answers each fetchone() with the next queued row."""

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
        return self

    def fetchone(self):
        return self.rows.pop(0)


def use_connection(monkeypatch, connection):
    monkeypatch.setattr(auth, "get_connection", connection)
    monkeypatch.setattr(student_deletion, "get_connection", connection)


def delete_student(student_id=None, token="admin-token"):
    client.cookies.set("session", token)
    return client.delete(f"/api/admin/students/{student_id or uuid4()}")


def test_admin_deletes_student(monkeypatch):
    # Rows: admin session, deleted student.
    connection = FakeConnection({"role": "admin"}, {"id": uuid4()})
    use_connection(monkeypatch, connection)

    assert delete_student().status_code == 204
    assert "role = 'student'" in connection.queries[-1]


def test_unknown_student_returns_404(monkeypatch):
    use_connection(monkeypatch, FakeConnection({"role": "admin"}, None))

    response = delete_student()

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found"}


@pytest.mark.parametrize("session,status", [(None, 401), ({"role": "teacher"}, 403), ({"role": "student"}, 403)])
def test_only_logged_in_admins_can_delete(monkeypatch, session, status):
    connection = FakeConnection(session)
    use_connection(monkeypatch, connection)

    assert delete_student().status_code == status
    assert not any(query.startswith("DELETE") for query in connection.queries)


def test_database_failure_returns_503(monkeypatch):
    def unavailable():
        raise RuntimeError("DATABASE_URL is missing")

    monkeypatch.setattr(auth, "get_connection", FakeConnection({"role": "admin"}))
    monkeypatch.setattr(student_deletion, "get_connection", unavailable)

    assert delete_student().status_code == 503


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_delete_student_against_database():
    def user(role):
        return connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, 'test-only-encoded-hash', 'Test', 'User', %s) RETURNING id
        ''', (uuid4().hex + "@example.com", uuid4().hex, role)).fetchone()["id"]

    with get_connection() as connection:
        admin_id, teacher_id, student_id = user("admin"), user("teacher"), user("student")
        connection.execute("INSERT INTO teachers (user_id) VALUES (%s)", (teacher_id,))
        connection.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (student_id, uuid4().hex[:20]))
        class_id = connection.execute(
            "INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'French 101', 'fr') RETURNING id",
            (teacher_id,),
        ).fetchone()["id"]
        connection.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student_id))
        token = uuid4().hex
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 hour')",
            (sha256(token.encode()).hexdigest(), admin_id),
        )

    def exists(user_id):
        with get_connection() as connection:
            return connection.execute("SELECT id FROM users WHERE id = %s", (user_id,)).fetchone() is not None

    try:
        # A teacher's id is rejected, so this route cannot delete other account types.
        assert delete_student(teacher_id, token).status_code == 404
        assert exists(teacher_id)
        assert delete_student(student_id, token).status_code == 204
        assert not exists(student_id)
        with get_connection() as connection:
            assert connection.execute(
                "SELECT 1 FROM class_enrollments WHERE student_id = %s", (student_id,)
            ).fetchone() is None
            assert connection.execute("SELECT id FROM classes WHERE id = %s", (class_id,)).fetchone() is not None
    finally:
        with get_connection() as connection:
            connection.execute("DELETE FROM users WHERE id = ANY(%s)", ([admin_id, teacher_id, student_id],))
