from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import game_session
from main import app
from test_auth import FakeConnection
from utils import answer_check
from utils.ocr import InvalidPhoto, OCRUnavailable


@pytest.fixture
def api(monkeypatch):
    state = SimpleNamespace(candidates=[], queries=[], attempts=1, student=uuid4())
    state.location = {"building": "LIB", "room_number": "308", "current_position": 1, "finished_at": None, "difficulty": "basic"}
    state.location.update(latitude=49.94, longitude=-119.4, radius_metres=50)
    state.game = {"current_position": 1, "finished_at": None, "points": 0, "final_time_seconds": None}
    connection = FakeConnection(None)

    def execute(query, params):
        state.queries.append((query, params))
        row = [state.location, {"attempts": state.attempts}, state.game][len(state.queries) - 1]
        return SimpleNamespace(fetchone=lambda: row)

    monkeypatch.setattr(connection, "execute", execute)
    monkeypatch.setattr(game_session, "get_connection", connection)
    monkeypatch.setattr(game_session, "award_badges", lambda connection, student_id: [])
    monkeypatch.setattr(answer_check, "extract_room_numbers", lambda photo: state.candidates)
    app.dependency_overrides[game_session.require_student] = lambda: {"id": state.student, "role": "student"}
    with TestClient(app, base_url="https://testserver") as client:
        def submit(**changes):
            reading = dict(latitude=49.94, longitude=-119.4, accuracy=10,
                           captured_at=datetime.now(timezone.utc).isoformat())
            reading.update(changes)
            return client.post(f"/api/game/{uuid4()}/answer", content=b"photo", params=reading)
        state.submit = submit
        yield state
    app.dependency_overrides.clear()


@pytest.mark.parametrize("building,room,candidates,correct", [
    ("LIB", "308", ["LIB 308"], True), ("EME", "0050", ["EME 0050"], True),
    ("LIB", "308", [], False), ("LIB", "308", ["LIB 309"], False),
    ("LIB", "308", ["SCI 308"], False), ("EME", "0050", ["EME 50"], False)])
def test_photo_matches_owned_target_and_awards_only_correct_answers(api, building, room, candidates, correct):
    api.location.update(building=building, room_number=room)
    api.candidates = candidates
    api.game.update(current_position=2 if correct else 1, points=10 if correct else 0)
    response = api.submit()
    assert response.status_code == 200 and response.json()["correct"] == correct
    assert response.json()["points_awarded"] == response.json()["total_points"] == (10 if correct else 0)
    assert api.queries[0][1][1] == api.student and api.queries[2][1][-2:] == (api.student, 1)
    assert api.queries[2][1][2] == (10 if correct else 0)


@pytest.mark.parametrize("error,status", [(InvalidPhoto("Please retake the photo."), 422),
                                         (OCRUnavailable("private model details"), 503)])
def test_ocr_errors_are_safe_and_do_not_write(api, monkeypatch, error, status):
    def fail(photo):
        raise error
    monkeypatch.setattr(answer_check, "extract_room_numbers", fail)
    response = api.submit()
    assert response.status_code == status and "private" not in response.text
    assert len(api.queries) == 1


@pytest.mark.parametrize("difficulty,points", [("basic", 10), ("advanced", 20), ("expert", 30)])
@pytest.mark.parametrize("correct", [True, False])
def test_answer_uses_stored_difficulty(api, difficulty, points, correct):
    api.location["difficulty"] = difficulty
    api.candidates = ["LIB 308"] if correct else []
    awarded = points if correct else 0
    api.game.update(points=awarded, current_position=2 if correct else 1)
    response = api.submit()
    assert response.status_code == 200
    assert response.json()["points_awarded"] == awarded
    assert response.json()["total_points"] == awarded
    assert api.queries[2][1][2] == awarded


def test_invalid_stored_difficulty_does_not_write(api, caplog):
    api.location["difficulty"] = "invalid"
    api.candidates = ["LIB 308"]
    response = api.submit()
    assert response.status_code == 500
    assert response.json() == {"detail": "Could not calculate points. Please try again later."}
    assert len(api.queries) == 1
    assert "unsupported game difficulty" in caplog.text


@pytest.mark.parametrize("difficulty,second_points,minimum_points",
                         [("basic", 6, 3), ("advanced", 12, 6), ("expert", 18, 9)])
@pytest.mark.parametrize("attempt", [2, 3, 4, 10])
@pytest.mark.parametrize("correct", [True, False])
def test_answer_points_depend_on_recorded_attempt(api, difficulty, second_points, minimum_points, attempt, correct):
    api.location["difficulty"] = difficulty
    api.attempts = attempt
    api.candidates = ["LIB 308"] if correct else []
    awarded = (second_points if attempt == 2 else minimum_points) if correct else 0
    api.game.update(points=awarded, current_position=2 if correct else 1)
    response = api.submit()
    assert response.status_code == 200
    assert response.json()["attempts"] == attempt
    assert response.json()["points_awarded"] == response.json()["total_points"] == awarded
    assert api.queries[2][1][2] == awarded
@pytest.mark.parametrize("changes", [
    {"latitude": 49.95}, {"accuracy": 51}, {"latitude": "nan"},
    {"longitude": -181}, {"radius_metres": 999999},
])
def test_invalid_or_outside_gps_blocks_answer(api, changes):
    response = api.submit(**changes)
    assert response.status_code == 422
    assert len(api.queries) <= 1


def test_expired_gps_blocks_answer(api):
    response = api.submit(captured_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat())
    assert response.status_code == 422
    assert len(api.queries) == 1


def test_missing_target_blocks_answer(api):
    api.location.update(latitude=None, longitude=None, radius_metres=None)
    assert api.submit().status_code == 503
    assert len(api.queries) == 1
