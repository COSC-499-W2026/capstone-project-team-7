import os
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import admin
import auth
import teacher_deletion
from database import get_connection

app = FastAPI()
app.include_router(admin.router)
app.include_router(teacher_deletion.router)
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
    monkeypatch.setattr(teacher_deletion, "get_connection", connection)


def delete_teacher(teacher_id=None, token="admin-token"):
    client.cookies.set("session", token)
    return client.delete(f"/api/admin/teachers/{teacher_id or uuid4()}")


def deleted(connection):
    return any(query.startswith("DELETE") for query in connection.queries)


def test_admin_deletes_teacher_without_classes(monkeypatch):
    # Rows: admin session, locked teacher, class count.
    connection = FakeConnection({"role": "admin"}, {"user_id": uuid4()}, {"classes": 0})
    use_connection(monkeypatch, connection)

    assert delete_teacher().status_code == 204
    assert deleted(connection)


def test_teacher_with_classes_is_not_deleted(monkeypatch):
    connection = FakeConnection({"role": "admin"}, {"user_id": uuid4()}, {"classes": 2})
    use_connection(monkeypatch, connection)

    response = delete_teacher()

    assert response.status_code == 409
    assert response.json() == {"detail": "Reassign this teacher's classes before deleting them"}
    assert not deleted(connection)


def test_unknown_teacher_returns_404(monkeypatch):
    connection = FakeConnection({"role": "admin"}, None)
    use_connection(monkeypatch, connection)

    assert delete_teacher().status_code == 404
    assert not deleted(connection)


@pytest.mark.parametrize("session,status", [(None, 401), ({"role": "teacher"}, 403), ({"role": "student"}, 403)])
def test_only_logged_in_admins_can_delete(monkeypatch, session, status):
    connection = FakeConnection(session)
    use_connection(monkeypatch, connection)

    assert delete_teacher().status_code == status
    assert not deleted(connection)


def test_database_failure_returns_503(monkeypatch):
    def unavailable():
        raise RuntimeError("DATABASE_URL is missing")

    monkeypatch.setattr(auth, "get_connection", FakeConnection({"role": "admin"}))
    monkeypatch.setattr(teacher_deletion, "get_connection", unavailable)

    assert delete_teacher().status_code == 503


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL is not configured")
def test_delete_after_reassign_keeps_student_data():
    def user(role):
        return connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, 'test-only-encoded-hash', 'Test', 'User', %s) RETURNING id
        ''', (uuid4().hex + "@example.com", uuid4().hex, role)).fetchone()["id"]

    with get_connection() as connection:
        admin_id, old_teacher, new_teacher, student_id = user("admin"), user("teacher"), user("teacher"), user("student")
        for teacher in (old_teacher, new_teacher):
            connection.execute("INSERT INTO teachers (user_id) VALUES (%s)", (teacher,))
        connection.execute("INSERT INTO students (user_id, student_number) VALUES (%s, %s)", (student_id, uuid4().hex[:20]))
        class_id = connection.execute(
            "INSERT INTO classes (teacher_id, name, language_code) VALUES (%s, 'French 101', 'fr') RETURNING id",
            (old_teacher,),
        ).fetchone()["id"]
        connection.execute("INSERT INTO class_enrollments (class_id, student_id) VALUES (%s, %s)", (class_id, student_id))
        token = uuid4().hex
        connection.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (%s, %s, now() + interval '1 hour')",
            (sha256(token.encode()).hexdigest(), admin_id),
        )

    def enrollments():
        with get_connection() as connection:
            return connection.execute(
                "SELECT student_id FROM class_enrollments WHERE class_id = %s", (class_id,)
            ).fetchall()

    try:
        assert delete_teacher(old_teacher, token).status_code == 409
        assert enrollments() == [{"student_id": student_id}]
        with get_connection() as connection:
            connection.execute("UPDATE classes SET teacher_id = %s WHERE id = %s", (new_teacher, class_id))
        assert delete_teacher(old_teacher, token).status_code == 204
        assert enrollments() == [{"student_id": student_id}]
        with get_connection() as connection:
            assert connection.execute("SELECT id FROM users WHERE id = %s", (old_teacher,)).fetchone() is None
    finally:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM users WHERE id = ANY(%s)", ([admin_id, old_teacher, new_teacher, student_id],)
            )
