from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import auth
import icon_store
from database import get_connection
from main import app
from test_auth import FakeConnection
from test_student_enrollment import enrollment_db, login

STORE_URL = "/api/student/store"
USER = {"id": uuid4(), "role": "student"}


def redeem_url(icon_id):
    return f"{STORE_URL}/{icon_id}/redeem"


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


def add_games(*points):
    """Save one game per amount, each worth that many points."""
    with get_connection() as db:
        for amount in points:
            db.execute("""INSERT INTO game_sessions (student_id, language_code, difficulty, points)
                VALUES (%s, 'fr', 'basic', %s)""", (student_id(), amount))


def owned_icons():
    """Each owned icon and the points paid for it."""
    with get_connection() as db:
        rows = db.execute("SELECT icon_id, points_spent FROM student_icons WHERE student_id = %s",
                          (student_id(),)).fetchall()
    return {row["icon_id"]: row["points_spent"] for row in rows}


def test_redeeming_an_icon_spends_its_price(enrollment_db, client):
    add_games(80)
    login(client)
    response = client.post(redeem_url("croissant_cutie"))
    assert response.status_code == 201
    assert response.json() == {"icon_id": "croissant_cutie", "balance": 30}
    assert owned_icons() == {"croissant_cutie": 50}
    croissant = client.get(STORE_URL).json()["icons"][0]
    assert croissant["owned"] is True and croissant["equipped"] is False


def test_store_shows_balance_prices_and_owned_flags(enrollment_db, client):
    add_games(100, 60)
    login(client)
    client.post(redeem_url("croissant_cutie"))
    client.put("/api/student/profile/icon", json={"icon_id": "croissant_cutie"})
    assert client.get(STORE_URL).json() == {"balance": 110, "icons": [
        {"id": "croissant_cutie", "name": "Croissant Cutie", "owned": True, "equipped": True, "price": 50},
        {"id": "mac_the_macaron", "name": "Mac the Macaron", "owned": False, "equipped": False, "price": 100},
        {"id": "speedy_escargot", "name": "Speedy Escargot", "owned": False, "equipped": False, "price": 150},
    ]}


def test_balance_adds_every_game_and_free_icons_cost_nothing(enrollment_db, client):
    add_games(30, 40, 50)
    with get_connection() as db:
        db.execute("INSERT INTO student_icons (student_id, icon_id) VALUES (%s, 'speedy_escargot')", (student_id(),))
    login(client)
    assert client.get(STORE_URL).json()["balance"] == 120
    assert client.post(redeem_url("mac_the_macaron")).json()["balance"] == 20
    assert client.get(STORE_URL).json()["balance"] == 20


def test_not_enough_points_changes_nothing(enrollment_db, client):
    add_games(40)
    login(client)
    response = client.post(redeem_url("croissant_cutie"))
    assert response.status_code == 400
    assert response.json() == {"detail": "Not enough points"}
    assert owned_icons() == {}
    assert client.get(STORE_URL).json()["balance"] == 40


def test_redeeming_an_owned_icon_is_refused(enrollment_db, client):
    add_games(200)
    login(client)
    client.post(redeem_url("croissant_cutie"))
    response = client.post(redeem_url("croissant_cutie"))
    assert response.status_code == 409
    assert response.json() == {"detail": "You already own this icon"}
    assert owned_icons() == {"croissant_cutie": 50}
    assert client.get(STORE_URL).json()["balance"] == 150


@pytest.mark.parametrize("icon_id", ["not_an_icon", "speedy_escargot"])
def test_unknown_or_unpriced_icon_is_not_found(signed_in, monkeypatch, icon_id):
    monkeypatch.delitem(icon_store.ICON_PRICES, "speedy_escargot")
    def unexpected():
        raise AssertionError("should not connect")
    monkeypatch.setattr(icon_store, "get_connection", unexpected)
    response = signed_in.post(redeem_url(icon_id))
    assert response.status_code == 404
    assert response.json() == {"detail": "Profile icon not found"}


@pytest.mark.parametrize("method,url", [("GET", STORE_URL), ("POST", redeem_url("croissant_cutie"))])
def test_requires_login(client, monkeypatch, method, url):
    monkeypatch.setattr(auth, "get_connection", FakeConnection(None))
    assert client.request(method, url).status_code == 401


@pytest.mark.parametrize("role", ["teacher", "admin"])
@pytest.mark.parametrize("method,url", [("GET", STORE_URL), ("POST", redeem_url("croissant_cutie"))])
def test_non_students_are_forbidden(client, role, method, url):
    app.dependency_overrides[auth.current_user] = lambda: dict(USER, role=role)
    response = client.request(method, url)
    assert response.status_code == 403
    assert response.json() == {"detail": "Student access required"}


@pytest.mark.parametrize("method,url", [("GET", STORE_URL), ("POST", redeem_url("croissant_cutie"))])
def test_database_failure_is_safe(signed_in, monkeypatch, method, url):
    def unavailable():
        raise psycopg.OperationalError("private database details")
    monkeypatch.setattr(icon_store, "get_connection", unavailable)
    response = signed_in.request(method, url)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
