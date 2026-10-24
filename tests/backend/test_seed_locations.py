"""Seed script tests run in a temporary schema so they never touch real data."""

from utils.seed_locations import LOCATIONS, seed_locations
from test_seed_admin import connect  # noqa: F401  (reuses the temporary-schema fixture)


def french_clues(connect):
    with connect() as connection:
        return connection.execute(
            """SELECT locations.building, locations.room_number, location_clues.number_text
            FROM locations JOIN location_clues ON location_clues.location_id = locations.id
            WHERE location_clues.language_code = 'fr' ORDER BY building, room_number"""
        ).fetchall()


def test_demo_data_has_five_different_rooms_with_french_text():
    rooms = {(location["building"], location["room_number"]) for location in LOCATIONS}
    assert len(rooms) == len(LOCATIONS) == 5
    assert all(location["fr"][0] and location["fr"][1] for location in LOCATIONS)


def test_seeds_every_location_with_a_french_clue(connect):
    with connect() as connection:
        assert seed_locations(connection) == 5
    clues = french_clues(connect)
    assert len(clues) == 5
    assert {"building": "COM", "room_number": "316", "number_text": "trois cent seize"} in clues


def test_second_run_adds_nothing(connect):
    with connect() as connection:
        seed_locations(connection)
    with connect() as connection:
        assert seed_locations(connection) == 0
    assert len(french_clues(connect)) == 5


def test_adds_missing_clue_for_a_location_that_already_exists(connect):
    with connect() as connection:
        connection.execute("INSERT INTO locations (building, room_number) VALUES ('COM', '316')")
        assert seed_locations(connection) == 4
    assert len(french_clues(connect)) == 5
