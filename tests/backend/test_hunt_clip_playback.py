"""Hunt games play the clip the teacher chose for each room, and the default clip otherwise."""

from uuid import uuid4

from database import get_connection
from test_game_session import CLIP, add_clips
from test_hunt_progress import client, db, login
from utils.audio_storage import clip_path


def hunt_rooms():
    with get_connection() as conn:
        return [row["id"] for row in conn.execute("SELECT id FROM locations").fetchall()]


def choose_clip(db, location_id, retired=False, with_file=True):
    """The teacher's own Expert clip for the room, chosen for the hunt; its file holds the clip id."""
    with get_connection() as conn:
        clip_id = conn.execute("""INSERT INTO location_clips
            (location_id, language_code, difficulty, label, created_by, retired_at)
            VALUES (%s, 'fr', 'expert', 'Café clue', %s, CASE WHEN %s THEN now() END) RETURNING id""",
            (location_id, db["teacher"], retired)).fetchone()["id"]
        conn.execute("INSERT INTO hunt_clips (hunt_id, location_id, clip_id) VALUES (%s, %s, %s)",
                     (db["hunt"], location_id, clip_id))
    if with_file:
        path = clip_path("fr", clip_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(str(clip_id).encode())
    return clip_id


def start_hunt(client, db, name="student"):
    login(client, name)
    response = client.post(f"/api/student/hunts/{db['hunt']}/start")
    assert response.status_code == 201, response.text
    return response.json()["game_id"]


def round_clip(game_id, position=1):
    with get_connection() as conn:
        return conn.execute("""SELECT location_id, clip_id FROM game_session_locations
            WHERE game_session_id = %s AND position = %s""", (game_id, position)).fetchone()


def played(client, game_id):
    response = client.get(f"/api/game/{game_id}/clue/audio")
    assert response.status_code == 200, response.text
    return response.content


def test_hunt_game_saves_and_plays_the_chosen_clip(db, client):
    clips = {room: choose_clip(db, room) for room in hunt_rooms()}
    game_id = start_hunt(client, db)
    rounds = [round_clip(game_id, position) for position in range(1, 6)]
    assert all(row["clip_id"] == clips[row["location_id"]] for row in rounds)
    assert played(client, game_id) == str(rounds[0]["clip_id"]).encode()


def test_only_chosen_rooms_save_a_clip(db, client):
    chosen_room = hunt_rooms()[0]
    choose_clip(db, chosen_room)
    game_id = start_hunt(client, db)
    rounds = [round_clip(game_id, position) for position in range(1, 6)]
    assert [row["clip_id"] is not None for row in rounds] == [row["location_id"] == chosen_room for row in rounds]


def test_dashboard_game_plays_the_default_for_a_chosen_room(db, client):
    for room in hunt_rooms():
        choose_clip(db, room)
    login(client, "student")
    game_id = client.post("/api/game/start", json={"difficulty": "expert"}).json()["game_id"]
    assert round_clip(game_id)["clip_id"] is None
    assert played(client, game_id) == CLIP


def test_clip_retired_during_the_game_plays_the_default(db, client):
    for room in hunt_rooms():
        choose_clip(db, room)
    game_id = start_hunt(client, db)
    with get_connection() as conn:
        conn.execute("UPDATE location_clips SET retired_at = now() WHERE id = %s", (round_clip(game_id)["clip_id"],))
    assert played(client, game_id) == CLIP


def test_clip_retired_before_the_game_is_not_saved(db, client):
    for room in hunt_rooms():
        choose_clip(db, room, retired=True)
    game_id = start_hunt(client, db)
    assert round_clip(game_id)["clip_id"] is None
    assert played(client, game_id) == CLIP


def test_missing_clip_file_plays_the_default(db, client):
    for room in hunt_rooms():
        choose_clip(db, room, with_file=False)
    game_id = start_hunt(client, db)
    assert round_clip(game_id)["clip_id"] is not None
    assert played(client, game_id) == CLIP


def test_clue_response_never_shows_clip_details(db, client):
    for room in hunt_rooms():
        choose_clip(db, room)
    game_id = start_hunt(client, db)
    clue = client.get(f"/api/game/{game_id}/clue").json()
    assert set(clue) == {"position", "clue_id", "revision", "total_locations", "building", "audio_url",
                         "elapsed_seconds", "clue_elapsed_seconds"}
    assert "Café clue" not in str(clue)
    assert str(round_clip(game_id)["clip_id"]) not in str(clue)


def add_spare_room():
    """A sixth playable room, so a skip has one replacement."""
    with get_connection() as conn:
        room = conn.execute("""INSERT INTO locations (building, room_number, latitude, longitude, radius_metres)
            VALUES ('EME', %s, 49.94, -119.4, 50) RETURNING id""", (uuid4().hex,)).fetchone()["id"]
        conn.execute("""INSERT INTO location_clues (location_id, language_code, number_text, description_text)
            VALUES (%s, 'fr', 'cent', 'une salle')""", (room,))
    add_clips()
    return room


def skip(client, game_id):
    response = client.post(f"/api/game/{game_id}/skip?position=1&revision=0")
    assert response.status_code == 200, response.text
    return response.json()


def test_skip_onto_a_chosen_room_plays_its_clip(db, client):
    game_id = start_hunt(client, db)
    spare = add_spare_room()
    clip_id = choose_clip(db, spare)
    clue = skip(client, game_id)
    assert round_clip(game_id) == {"location_id": spare, "clip_id": clip_id}
    assert "clip" not in str(clue)
    assert played(client, game_id) == str(clip_id).encode()


def test_skip_onto_a_room_without_a_choice_plays_the_default(db, client):
    for room in hunt_rooms():
        choose_clip(db, room)
    game_id = start_hunt(client, db)
    spare = add_spare_room()
    skip(client, game_id)
    assert round_clip(game_id) == {"location_id": spare, "clip_id": None}
    assert played(client, game_id) == CLIP


def test_another_students_hunt_game_audio_is_not_found(db, client):
    for room in hunt_rooms():
        choose_clip(db, room)
    game_id = start_hunt(client, db)
    login(client, "classmate")
    response = client.get(f"/api/game/{game_id}/clue/audio")
    assert (response.status_code, response.json()) == (404, {"detail": "Game not found"})
