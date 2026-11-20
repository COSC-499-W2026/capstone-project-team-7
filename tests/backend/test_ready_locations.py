import pytest

from database import get_connection
from test_game_session import add_locations, client, game_db, game_locations, login, URL
from utils.audio_storage import audio_path
from utils.ready_locations import ready_location_ids


def remove_gps(location_id):
    with get_connection() as db:
        db.execute("UPDATE locations SET latitude = NULL, longitude = NULL, radius_metres = NULL WHERE id = %s",
                   (location_id,))


def remove_clip(location_id, difficulty, language_code="fr"):
    with get_connection() as db:
        location = db.execute("SELECT building, room_number FROM locations WHERE id = %s", (location_id,)).fetchone()
    audio_path(language_code, location, difficulty).unlink()


def ready(language_code, difficulty):
    with get_connection() as db:
        return set(ready_location_ids(db, language_code, difficulty))


def test_location_with_gps_and_a_clip_is_ready(game_db):
    french = add_locations(2, "fr")
    assert ready("fr", "basic") == set(french)


def test_location_without_gps_is_not_ready(game_db):
    french = add_locations(2, "fr")
    remove_gps(french[0])
    assert ready("fr", "basic") == {french[1]}


@pytest.mark.parametrize("difficulty", ["basic", "advanced", "expert"])
def test_location_without_a_clip_for_the_difficulty_is_not_ready_for_it(game_db, difficulty):
    french = add_locations(2, "fr")
    remove_clip(french[0], difficulty)
    assert ready("fr", difficulty) == {french[1]}
    others = [level for level in ("basic", "advanced", "expert") if level != difficulty]
    assert all(ready("fr", level) == set(french) for level in others)


def test_location_without_a_clue_in_the_language_is_not_ready(game_db):
    add_locations(2, "es")
    assert ready("fr", "basic") == set()


def test_game_never_picks_a_location_that_is_not_ready(game_db, client):
    french = add_locations(6, "fr")
    remove_gps(french[0])
    login(client)
    for _ in range(5):
        response = client.post(URL)
        assert response.status_code == 201
        assert {row["location_id"] for row in game_locations(response.json()["game_id"])} == set(french[1:])


def test_advanced_game_skips_a_location_with_only_a_basic_clip(game_db, client):
    french = add_locations(6, "fr")
    remove_clip(french[0], "advanced")
    login(client)
    advanced = client.post(URL, json={"difficulty": "advanced"})
    assert advanced.status_code == 201
    assert {row["location_id"] for row in game_locations(advanced.json()["game_id"])} == set(french[1:])


def test_basic_game_can_still_pick_a_location_with_only_a_basic_clip(game_db, client):
    french = add_locations(5, "fr")
    remove_clip(french[0], "advanced")
    login(client)
    basic = client.post(URL)
    assert basic.status_code == 201
    assert {row["location_id"] for row in game_locations(basic.json()["game_id"])} == set(french)


def test_fewer_than_five_ready_locations_is_a_conflict(game_db, client):
    french = add_locations(5, "fr")
    remove_clip(french[0], "expert")
    login(client)
    response = client.post(URL, json={"difficulty": "expert"})
    assert response.status_code == 409
    assert response.json() == {"detail": "Not enough locations for this language yet"}
    with get_connection() as db:
        assert db.execute("SELECT count(*) FROM game_sessions").fetchone()["count"] == 0

