from uuid import uuid4

import pytest

import location_creation
from database import get_connection
from test_teacher_access import access_db, client, login
from test_teacher_locations import add_location, audio_dir, locations_url

LIB_305 = {"building": "LIB", "room_number": "305", "number_text": "trois cent cinq",
           "description_text": "La salle d'étude au troisième étage"}
GPS = {"latitude": 49.9401, "longitude": -119.3956}


def rows(query, params=()):
    with get_connection() as db:
        return db.execute(query, params).fetchall()


def spanish_class():
    with get_connection() as db:
        return str(db.execute("""INSERT INTO classes (teacher_id, name, language_code)
            SELECT id, 'Spanish', 'es' FROM users WHERE username = 'teacher' RETURNING id""").fetchone()["id"])


def test_added_location_is_saved_with_its_gps_and_listed(access_db, audio_dir, client):
    login(client)
    response = client.post(locations_url(access_db), json={**LIB_305, **GPS})
    assert response.status_code == 201
    location = response.json()
    assert location == {"id": location["id"], "building": "LIB", "room_number": "305", **GPS, "radius_metres": 50}
    assert [item["id"] for item in client.get(locations_url(access_db)).json()] == [location["id"]]
    assert rows("""SELECT language_code, number_text, description_text FROM location_clues""") == [
        {"language_code": "fr", "number_text": "trois cent cinq",
         "description_text": "La salle d'étude au troisième étage"}]
    assert rows("""SELECT users.username FROM locations JOIN users ON users.id = locations.created_by""") == [
        {"username": "teacher"}]


def test_location_without_gps_has_no_target(access_db, client):
    login(client)
    response = client.post(locations_url(access_db), json=LIB_305)
    assert response.status_code == 201
    assert {key: response.json()[key] for key in ("latitude", "longitude", "radius_metres")} == {
        "latitude": None, "longitude": None, "radius_metres": None}


def test_building_is_saved_in_uppercase(access_db, client):
    login(client)
    response = client.post(locations_url(access_db), json={**LIB_305, "building": " lib ", "room_number": " 305 "})
    assert response.status_code == 201
    assert (response.json()["building"], response.json()["room_number"]) == ("LIB", "305")


def test_existing_room_gets_the_clue_in_another_language(access_db, client):
    existing = add_location("COM", "316")
    login(client)
    response = client.post(locations_url(spanish_class()), json={
        "building": "COM", "room_number": "316", "number_text": "trescientos dieciséis",
        "description_text": "Un aula grande", **GPS})
    assert response.status_code == 201
    assert response.json()["id"] == existing
    assert rows("SELECT latitude, created_by FROM locations") == [{"latitude": None, "created_by": None}]
    assert rows("SELECT language_code FROM location_clues ORDER BY language_code") == [
        {"language_code": "es"}, {"language_code": "fr"}]


def test_room_with_a_clue_in_the_language_is_a_conflict(access_db, client):
    login(client)
    assert client.post(locations_url(access_db), json=LIB_305).status_code == 201
    response = client.post(locations_url(access_db), json={**LIB_305, "number_text": "autre"})
    assert response.status_code == 409
    assert response.json() == {"detail": "This room already has a clue in this language"}
    assert rows("SELECT number_text FROM location_clues") == [{"number_text": "trois cent cinq"}]


@pytest.mark.parametrize("change", [
    {"room_number": " "}, {"building": "C OM"}, {"building": "XYZ"}, {"room_number": "31A"},
    {"building": "EME", "room_number": "305"}, {"number_text": ""}, {"description_text": "  "},
    {"latitude": 49.94}, {"longitude": -119.39}, {"latitude": 91, "longitude": 0},
    {"latitude": 0, "longitude": 181}, {"radius_metres": 10},
])
def test_invalid_location_is_rejected_and_nothing_is_saved(access_db, client, change):
    login(client)
    assert client.post(locations_url(access_db), json={**LIB_305, **change}).status_code == 422
    assert rows("SELECT id FROM locations") == []


def test_other_teachers_class_is_not_found(access_db, client):
    login(client, "teacher2")
    response = client.post(locations_url(access_db), json=LIB_305)
    assert response.status_code == 404
    assert response.json() == {"detail": "Class not found"}
    assert rows("SELECT id FROM locations") == []


def test_unknown_class_is_not_found(access_db, client):
    login(client)
    assert client.post(locations_url(uuid4()), json=LIB_305).status_code == 404


def test_missing_session_and_students_are_rejected(access_db, client):
    assert client.post(locations_url(access_db), json=LIB_305).status_code == 401
    login(client, "student")
    assert client.post(locations_url(access_db), json=LIB_305).status_code == 403


def test_database_failure_returns_503(access_db, client, monkeypatch):
    login(client)

    def unavailable():
        raise RuntimeError("database down")

    monkeypatch.setattr(location_creation, "get_connection", unavailable)
    response = client.post(locations_url(access_db), json=LIB_305)
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
