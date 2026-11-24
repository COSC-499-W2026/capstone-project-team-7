from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import student_icons
from database import get_connection
from main import app
from test_auth import FakeConnection
from test_student_enrollment import enrollment_db, login

LIST_URL = "/api/student/icons"
EQUIP_URL = "/api/student/profile/icon"
PROFILE_URL = "/api/student/profile"
USER = {"id": uuid4(), "role": "student"}


@pytest.fixture
def client():
    # HTTPS allows TestClient to send the login endpoint's Secure cookie.
    with TestClient(app, base_url="https://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def signed_in(client):
    app.dependency_overrides[auth.current_user] = lambda: USER
    return client


def student_id():
    with get_connection() as db:
        return db.execute("SELECT id FROM users WHERE username = 'student'").fetchone()["id"]


def give_icons():
    """Own Croissant Cutie and Mac the Macaron, but not Speedy Escargot."""
    with get_connection() as db:
        for icon_id in ("croissant_cutie", "mac_the_macaron"):
            db.execute("INSERT INTO student_icons (student_id, icon_id) VALUES (%s, %s)", (student_id(), icon_id))


def equipped_icon():
    with get_connection() as db:
        return db.execute("SELECT equipped_icon_id FROM students WHERE user_id = %s",
                          (student_id(),)).fetchone()["equipped_icon_id"]


def test_equip_owned_icon_is_saved_and_returned_by_profile(enrollment_db, client):
    give_icons()
    login(client)
    response = client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"})
    assert response.status_code == 200
    assert response.json() == {"profile_icon": "croissant_cutie"}
    assert equipped_icon() == "croissant_cutie"
    assert client.get(PROFILE_URL).json()["profile_icon"] == "croissant_cutie"


def test_switching_between_owned_icons_keeps_the_latest(enrollment_db, client):
    give_icons()
    login(client)
    client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"})
    assert client.put(EQUIP_URL, json={"icon_id": "mac_the_macaron"}).status_code == 200
    assert client.get(PROFILE_URL).json()["profile_icon"] == "mac_the_macaron"


def test_equipping_unowned_icon_keeps_the_previous_one(enrollment_db, client):
    give_icons()
    login(client)
    client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"})
    response = client.put(EQUIP_URL, json={"icon_id": "speedy_escargot"})
    assert response.status_code == 403
    assert response.json() == {"detail": "You don't own this profile icon"}
    assert equipped_icon() == "croissant_cutie"
    assert client.get(PROFILE_URL).json()["profile_icon"] == "croissant_cutie"


def test_equipping_unknown_icon_keeps_the_previous_one(enrollment_db, client):
    give_icons()
    login(client)
    client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"})
    response = client.put(EQUIP_URL, json={"icon_id": "not_an_icon"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Profile icon not found"}
    assert equipped_icon() == "croissant_cutie"


def test_student_with_no_icons_cannot_equip(enrollment_db, client):
    login(client)
    assert client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"}).status_code == 403
    assert equipped_icon() is None
    assert client.get(PROFILE_URL).json()["profile_icon"] is None


def test_list_marks_owned_and_equipped(enrollment_db, client):
    give_icons()
    login(client)
    client.put(EQUIP_URL, json={"icon_id": "mac_the_macaron"})
    assert client.get(LIST_URL).json() == [
        {"id": "croissant_cutie", "name": "Croissant Cutie", "owned": True, "equipped": False},
        {"id": "mac_the_macaron", "name": "Mac the Macaron", "owned": True, "equipped": True},
        {"id": "speedy_escargot", "name": "Speedy Escargot", "owned": False, "equipped": False},
    ]


def test_new_student_owns_nothing(enrollment_db, client):
    login(client)
    icons = client.get(LIST_URL).json()
    assert len(icons) == 3
    assert not any(icon["owned"] or icon["equipped"] for icon in icons)


def test_one_students_icons_do_not_affect_another(enrollment_db, client):
    with get_connection() as db:
        other = db.execute("""INSERT INTO users
            (email, username, password, first_name, last_name, role)
            VALUES ('other@example.com', 'other', 'hash', 'Other', 'User', 'student') RETURNING id""").fetchone()["id"]
        db.execute("INSERT INTO students (user_id, student_number) VALUES (%s, '99999999')", (other,))
        db.execute("INSERT INTO student_icons (student_id, icon_id) VALUES (%s, 'speedy_escargot')", (other,))
    give_icons()
    login(client)
    assert client.put(EQUIP_URL, json={"icon_id": "speedy_escargot"}).status_code == 403
    assert not next(icon for icon in client.get(LIST_URL).json() if icon["id"] == "speedy_escargot")["owned"]


def test_database_refuses_an_unowned_equipped_icon(enrollment_db):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with get_connection() as db:
            db.execute("UPDATE students SET equipped_icon_id = 'speedy_escargot' WHERE user_id = %s",
                       (student_id(),))
    assert equipped_icon() is None


def test_deleting_a_student_with_an_equipped_icon_works(enrollment_db, client):
    give_icons()
    login(client)
    client.put(EQUIP_URL, json={"icon_id": "croissant_cutie"})
    removed = student_id()
    with get_connection() as db:
        db.execute("DELETE FROM users WHERE id = %s", (removed,))
        assert db.execute("SELECT 1 FROM student_icons WHERE student_id = %s", (removed,)).fetchone() is None


@pytest.mark.parametrize("body", [{}, {"icon_id": None}, {"icon_id": 7}, {"icon_id": "x" * 51},
                                  {"icon_id": "croissant_cutie", "extra": 1}])
def test_bad_body_is_rejected(signed_in, body):
    assert signed_in.put(EQUIP_URL, json=body).status_code == 422


def test_unknown_icon_never_reaches_the_database(signed_in, monkeypatch):
    def unexpected():
        raise AssertionError("should not connect")
    monkeypatch.setattr(student_icons, "get_connection", unexpected)
    assert signed_in.put(EQUIP_URL, json={"icon_id": "not_an_icon"}).status_code == 404


@pytest.mark.parametrize("method,url,body", [("GET", LIST_URL, None),
                                             ("PUT", EQUIP_URL, {"icon_id": "croissant_cutie"})])
def test_requires_login(client, monkeypatch, method, url, body):
    monkeypatch.setattr(auth, "get_connection", FakeConnection(None))
    assert client.request(method, url, json=body).status_code == 401


@pytest.mark.parametrize("role", ["teacher", "admin"])
@pytest.mark.parametrize("method,url,body", [("GET", LIST_URL, None),
                                             ("PUT", EQUIP_URL, {"icon_id": "croissant_cutie"})])
def test_non_students_are_forbidden(client, role, method, url, body):
    app.dependency_overrides[auth.current_user] = lambda: dict(USER, role=role)
    response = client.request(method, url, json=body)
    assert response.status_code == 403
    assert response.json() == {"detail": "Student access required"}


@pytest.mark.parametrize("error", [RuntimeError("private details"), psycopg.OperationalError("secret")])
@pytest.mark.parametrize("method,url,body", [("GET", LIST_URL, None),
                                             ("PUT", EQUIP_URL, {"icon_id": "croissant_cutie"})])
def test_database_failure_is_safe(signed_in, monkeypatch, error, method, url, body):
    def unavailable():
        raise error
    monkeypatch.setattr(student_icons, "get_connection", unavailable)
    response = signed_in.request(method, url, json=body)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
