from datetime import date, timedelta
from uuid import uuid4

import psycopg
import pytest

import hunt_assignment
import teacher_access
from database import get_connection
from test_teacher_access import access_db, client, login
from test_teacher_locations import COM, add_location

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


def add_clip(location_id, owner="teacher", language_code="fr", difficulty="basic", retired=False):
    """Save a clip row straight to the database; hunts only need the row, not the file."""
    with get_connection() as db:
        return str(db.execute("""INSERT INTO location_clips
            (location_id, language_code, difficulty, label, created_by, retired_at)
            SELECT %s, %s, %s, 'Café clue', id, CASE WHEN %s THEN now() END FROM users WHERE username = %s
            RETURNING id""", (location_id, language_code, difficulty, retired, owner)).fetchone()["id"])


def saved_choices():
    with get_connection() as db:
        return [(str(row["location_id"]), str(row["clip_id"]))
                for row in db.execute("SELECT location_id, clip_id FROM hunt_clips").fetchall()]


def choice(location_id, clip_id):
    return {"location_id": location_id, "clip_id": clip_id}


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


def test_hunt_saves_and_lists_clip_choices(access_db, client):
    com, ask = add_location("COM", "316"), add_location("ASC", "140")
    com_clip, ask_clip = add_clip(com), add_clip(ask)
    login(client)
    response = assign(client, access_db, clips=[choice(com, com_clip), choice(ask, ask_clip)])
    assert response.status_code == 201
    assert "clips" not in response.json()
    assert sorted(saved_choices()) == sorted([(com, com_clip), (ask, ask_clip)])
    [hunt] = client.get(URL.format(access_db)).json()
    assert hunt["clips"] == [
        {"location_id": ask, "building": "ASC", "room_number": "140", "clip_id": ask_clip, "label": "Café clue"},
        {"location_id": com, **COM, "clip_id": com_clip, "label": "Café clue"},
    ]


def test_hunt_without_clip_choices_lists_none(access_db, client):
    login(client)
    assert assign(client, access_db).status_code == 201
    assert assign(client, access_db, clips=[]).status_code == 201
    assert [hunt["clips"] for hunt in client.get(URL.format(access_db)).json()] == [[], []]
    assert saved_choices() == []


def test_retired_clip_is_left_out_of_the_hunt_list(access_db, client):
    location_id = add_location("COM", "316")
    clip_id = add_clip(location_id)
    login(client)
    assign(client, access_db, clips=[choice(location_id, clip_id)])
    with get_connection() as db:
        db.execute("UPDATE location_clips SET retired_at = now() WHERE id = %s", (clip_id,))
    assert client.get(URL.format(access_db)).json()[0]["clips"] == []
    assert saved_choices() == [(location_id, clip_id)]


def reassign_class(class_id, username):
    with get_connection() as db:
        db.execute("UPDATE classes SET teacher_id = (SELECT id FROM users WHERE username = %s) WHERE id = %s",
                   (username, class_id))


def add_choice(hunt_id, location_id, clip_id):
    with get_connection() as db:
        db.execute("INSERT INTO hunt_clips (hunt_id, location_id, clip_id) VALUES (%s, %s, %s)",
                   (hunt_id, location_id, clip_id))


def test_reassigned_class_hides_previous_teachers_clips(access_db, client):
    location_id = add_location("COM", "316")
    login(client)
    assign(client, access_db, clips=[choice(location_id, add_clip(location_id))])
    reassign_class(access_db, "teacher2")
    login(client, "teacher2")
    [hunt] = client.get(URL.format(access_db)).json()
    assert hunt["clips"] == []
    assert len(saved_choices()) == 1


def test_reassigned_teacher_sees_only_their_own_clips(access_db, client):
    com, ask = add_location("COM", "316"), add_location("ASC", "140")
    login(client)
    hunt_id = assign(client, access_db, clips=[choice(com, add_clip(com))]).json()["id"]
    reassign_class(access_db, "teacher2")
    own_clip = add_clip(ask, owner="teacher2")
    add_choice(hunt_id, ask, own_clip)
    login(client, "teacher2")
    [hunt] = client.get(URL.format(access_db)).json()
    assert [clip["clip_id"] for clip in hunt["clips"]] == [own_clip]


@pytest.mark.parametrize("clip", [
    {"owner": "teacher2"},
    {"difficulty": "expert"},
    {"language_code": "es"},
    {"retired": True},
], ids=["other teacher", "wrong difficulty", "other language", "retired"])
def test_unusable_clip_is_rejected_and_nothing_is_saved(access_db, client, clip):
    location_id = add_location("COM", "316", clip.get("language_code", "fr"))
    clip_id = add_clip(location_id, **clip)
    login(client)
    response = assign(client, access_db, clips=[choice(location_id, clip_id)])
    assert response.status_code == 422
    assert response.json() == {"detail": "Your clip for COM 316 can't be used in this hunt"}
    assert assigned_hunts() == []
    assert saved_choices() == []


def test_clip_for_a_different_room_is_rejected(access_db, client):
    com, ask = add_location("COM", "316"), add_location("ASC", "140")
    clip_id = add_clip(com)
    login(client)
    response = assign(client, access_db, clips=[choice(ask, clip_id)])
    assert response.status_code == 422
    assert response.json() == {"detail": "Your clip for ASC 140 can't be used in this hunt"}
    assert assigned_hunts() == []


def test_unknown_clip_or_room_is_rejected(access_db, client):
    location_id = add_location("COM", "316")
    login(client)
    for body in (choice(location_id, str(uuid4())), choice(str(uuid4()), add_clip(location_id))):
        response = assign(client, access_db, clips=[body])
        assert response.status_code == 422
        assert "can't be used in this hunt" in response.json()["detail"]
    assert assigned_hunts() == []


def test_one_bad_choice_rejects_the_whole_hunt(access_db, client):
    com, ask = add_location("COM", "316"), add_location("ASC", "140")
    clips = [choice(com, add_clip(com)), choice(ask, add_clip(ask, owner="teacher2"))]
    login(client)
    response = assign(client, access_db, clips=clips)
    assert response.status_code == 422
    assert assigned_hunts() == []
    assert saved_choices() == []


@pytest.mark.parametrize("clips", [
    "duplicate",
    [{"location_id": str(uuid4())}],
    [{"location_id": "not-a-uuid", "clip_id": str(uuid4())}],
    [{"location_id": str(uuid4()), "clip_id": str(uuid4()), "label": "extra"}],
    [{"location_id": str(uuid4()), "clip_id": str(uuid4())} for _ in range(21)],
], ids=["duplicate room", "missing clip", "bad id", "extra field", "too many"])
def test_invalid_clip_choices_are_rejected(access_db, client, clips):
    if clips == "duplicate":
        location_id = add_location("COM", "316")
        clips = [choice(location_id, add_clip(location_id)), choice(location_id, add_clip(location_id))]
    login(client)
    response = assign(client, access_db, clips=clips)
    assert response.status_code == 422
    assert assigned_hunts() == []
    assert saved_choices() == []


def test_duplicate_room_message_is_friendly(access_db, client):
    location_id = add_location("COM", "316")
    clip_id = add_clip(location_id)
    login(client)
    response = assign(client, access_db, clips=[choice(location_id, clip_id)] * 2)
    assert "Choose only one clip per room" in response.text


def test_deleting_a_hunt_removes_its_clip_choices(access_db, client):
    location_id = add_location("COM", "316")
    clip_id = add_clip(location_id)
    login(client)
    hunt_id = assign(client, access_db, clips=[choice(location_id, clip_id)]).json()["id"]
    assert client.delete(hunt_url(access_db, hunt_id)).status_code == 204
    assert saved_choices() == []
    with get_connection() as db:
        assert db.execute("SELECT retired_at FROM location_clips WHERE id = %s", (clip_id,)).fetchone()


def test_failed_clip_choice_save_keeps_no_hunt(access_db, client, monkeypatch):
    location_id = add_location("COM", "316")
    clip_id = add_clip(location_id)
    login(client)
    def fail(*args):
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(hunt_assignment, "save_clip_choices", fail)
    response = assign(client, access_db, clips=[choice(location_id, clip_id)])
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert assigned_hunts() == []
