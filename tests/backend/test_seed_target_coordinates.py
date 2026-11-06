import os

import psycopg
import pytest

from utils.seed_target_coordinates import DEMO_RADIUS_METRES, seed_target_coordinates

DEMO = {"building": "COM", "room_number": "316",
        "coordinates": (49.94072817380431, -119.39550274685362)}


@pytest.fixture
def db():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run coordinate seed integration tests")
    with psycopg.connect(url, autocommit=True) as connection:
        # The dependency PRs are not on main yet; exercise their expected table shape.
        connection.execute("""CREATE TEMP TABLE locations (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            building TEXT NOT NULL, room_number TEXT NOT NULL,
            latitude DOUBLE PRECISION, longitude DOUBLE PRECISION,
            radius_metres DOUBLE PRECISION,
            UNIQUE (building, room_number)
        )""")
        yield connection


def add_location(db, building="COM", room="316"):
    db.execute("INSERT INTO locations (building, room_number) VALUES (%s, %s)",
               (building, room))


def test_saves_supplied_coordinates_and_50_metre_radius(db):
    add_location(db)
    seed_target_coordinates(db, [DEMO])
    assert DEMO_RADIUS_METRES == 50
    assert db.execute("SELECT latitude, longitude, radius_metres FROM locations").fetchone() == (
        *DEMO["coordinates"], 50,
    )


def test_repeat_run_preserves_location_id_without_duplicates(db):
    add_location(db)
    seed_target_coordinates(db, [DEMO])
    before = db.execute("SELECT * FROM locations").fetchall()
    seed_target_coordinates(db, [DEMO])
    assert db.execute("SELECT * FROM locations").fetchall() == before


def test_does_not_change_other_targets(db):
    add_location(db)
    add_location(db, "LIB", "312")
    seed_target_coordinates(db, [DEMO])
    assert db.execute("""SELECT latitude, longitude, radius_metres FROM locations
        WHERE building = 'LIB'""").fetchone() == (None, None, None)


def test_missing_target_rolls_back_all_coordinate_updates(db):
    add_location(db)
    missing = dict(DEMO, room_number="missing")
    with pytest.raises(ValueError, match="Run the demo location seed first"):
        seed_target_coordinates(db, [DEMO, missing])
    assert db.execute("SELECT latitude, longitude, radius_metres FROM locations").fetchone() == (
        None, None, None,
    )
