from datetime import date, timedelta
from uuid import uuid4

import psycopg
import pytest

import hunt_assignment
import teacher_access
from database import get_connection
from test_teacher_access import access_db, client, login

URL = "/api/teacher/classes/{}/hunts"


def assigned_hunts():
    with get_connection() as db:
        return db.execute("SELECT class_id, language_code, difficulty, due_date FROM assigned_hunts").fetchall()


def other_teachers_class():
    with get_connection() as db:
        return str(db.execute("SELECT id FROM classes WHERE name = 'teacher2'").fetchone()["id"])


def assign(client, class_id, **body):
    return client.post(URL.format(class_id), json={"difficulty": "basic", **body})


def add_hunt(class_id):
    """Save a hunt straight to the database, e.g. in a class the logged-in teacher doesn't own."""
    with get_connection() as db:
        return str(db.execute("""INSERT INTO assigned_hunts (class_id, language_code, difficulty)
            VALUES (%s, 'fr', 'basic') RETURNING id""", (class_id,)).fetchone()["id"])


def hunt_url(class_id, hunt_id):
    return f"{URL.format(class_id)}/{hunt_id}"


def test_teacher_assigns_basic_hunt_with_class_language(access_db, client):
    login(client)
    response = assign(client, access_db)
    assert response.status_code == 201
    body = response.json()
    assert body == {"id": body["id"], "class_id": access_db, "language_code": "fr",
                    "difficulty": "basic", "due_date": None}
    assert [(str(row["class_id"]), row["language_code"], row["difficulty"], row["due_date"])
            for row in assigned_hunts()] == [(access_db, "fr", "basic", None)]


def test_teacher_assigns_hunt_with_future_due_date(access_db, client):
    login(client)
    due_date = date.today() + timedelta(days=7)
    response = assign(client, access_db, difficulty="expert", due_date=due_date.isoformat())
    assert response.status_code == 201
    assert response.json()["due_date"] == due_date.isoformat()
    assert [row["due_date"] for row in assigned_hunts()] == [due_date]


def test_same_hunt_can_be_assigned_twice(access_db, client):
    login(client)
    assert assign(client, access_db).status_code == 201
    assert assign(client, access_db).status_code == 201
    assert len(assigned_hunts()) == 2


def test_class_with_a_hunt_cannot_be_deleted(access_db, client):
    login(client)
    assert assign(client, access_db).status_code == 201
    with pytest.raises(psycopg.errors.ForeignKeyViolation), get_connection() as db:
        db.execute("DELETE FROM classes WHERE id = %s", (access_db,))
    assert len(assigned_hunts()) == 1


def test_class_without_hunts_can_still_be_deleted(access_db):
    with get_connection() as db:
        db.execute("DELETE FROM classes WHERE id = %s", (access_db,))
        assert db.execute("SELECT id FROM classes WHERE id = %s", (access_db,)).fetchone() is None


def test_other_teachers_class_is_forbidden(access_db, client):
    login(client)
    response = assign(client, other_teachers_class())
    assert response.status_code == 403
    assert response.json() == {"detail": "You can only assign hunts to your own classes"}
    assert assigned_hunts() == []


def test_missing_class_is_not_found(access_db, client):
    login(client)
    response = assign(client, uuid4())
    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}
    assert assigned_hunts() == []


@pytest.mark.parametrize("body", [{}, {"difficulty": "impossible"}, {"difficulty": None},
                                  {"difficulty": "basic", "language_code": "es"},
                                  {"difficulty": "basic", "due_date": "not-a-date"}])
def test_invalid_body_is_rejected(access_db, client, body):
    login(client)
    assert client.post(URL.format(access_db), json=body).status_code == 422
    assert assigned_hunts() == []


def test_past_due_date_is_rejected(access_db, client):
    login(client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    response = assign(client, access_db, due_date=yesterday)
    assert response.status_code == 422
    assert "Due date cannot be in the past" in response.text
    assert assigned_hunts() == []


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_requires_teacher(access_db, client, role, status):
    if role:
        login(client, role)
    assert assign(client, access_db).status_code == status
    assert assigned_hunts() == []


def test_teacher_lists_class_hunts_newest_first(access_db, client):
    login(client)
    due_date = (date.today() + timedelta(days=7)).isoformat()
    assign(client, access_db)
    assign(client, access_db, difficulty="expert", due_date=due_date)
    response = client.get(URL.format(access_db))
    assert response.status_code == 200
    hunts = response.json()
    assert [(hunt["difficulty"], hunt["due_date"]) for hunt in hunts] == [("expert", due_date), ("basic", None)]
    assert all(hunt["id"] and hunt["assigned_at"] for hunt in hunts)


def test_class_without_hunts_lists_nothing(access_db, client):
    login(client)
    response = client.get(URL.format(access_db))
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("class_id", [other_teachers_class, uuid4])
def test_listing_another_teachers_or_missing_class_is_not_found(access_db, client, class_id):
    login(client)
    response = client.get(URL.format(class_id()))
    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_listing_requires_teacher(access_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(URL.format(access_db)).status_code == status


def test_listing_database_failure_is_safe(access_db, client, monkeypatch):
    login(client)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(teacher_access, "get_connection", unavailable)
    response = client.get(URL.format(access_db))
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_teacher_deletes_a_hunt(access_db, client):
    login(client)
    kept = assign(client, access_db).json()["id"]
    deleted = assign(client, access_db, difficulty="expert").json()["id"]
    assert client.delete(hunt_url(access_db, deleted)).status_code == 204
    assert [hunt["id"] for hunt in client.get(URL.format(access_db)).json()] == [kept]


def test_deleting_a_missing_hunt_or_one_from_another_class_is_not_found(access_db, client):
    login(client)
    for hunt_id in (uuid4(), add_hunt(other_teachers_class())):
        response = client.delete(hunt_url(access_db, hunt_id))
        assert response.status_code == 404
        assert response.json() == {"detail": "Hunt not found"}
    assert len(assigned_hunts()) == 1


def test_deleting_from_another_teachers_class_is_not_found(access_db, client):
    login(client)
    other_class = other_teachers_class()
    response = client.delete(hunt_url(other_class, add_hunt(other_class)))
    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}
    assert len(assigned_hunts()) == 1


@pytest.mark.parametrize("role,status", [(None, 401), ("student", 403), ("admin", 403)])
def test_deleting_requires_teacher(access_db, client, role, status):
    hunt_id = add_hunt(access_db)
    if role:
        login(client, role)
    assert client.delete(hunt_url(access_db, hunt_id)).status_code == status
    assert len(assigned_hunts()) == 1


def test_deleting_database_failure_is_safe(access_db, client, monkeypatch):
    login(client)
    hunt_id = add_hunt(access_db)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(hunt_assignment, "get_connection", unavailable)
    response = client.delete(hunt_url(access_db, hunt_id))
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_database_failure_is_safe(access_db, client, monkeypatch):
    login(client)
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(hunt_assignment, "get_connection", unavailable)
    response = assign(client, access_db)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
