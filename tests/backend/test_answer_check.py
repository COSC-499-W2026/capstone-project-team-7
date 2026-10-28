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
    state = SimpleNamespace(candidates=[], queries=[], student=uuid4())
    state.location = {"building": "LIB", "room_number": "308", "current_position": 1, "finished_at": None}
    state.location.update(latitude=49.94, longitude=-119.4, radius_metres=50)
    state.game = {"current_position": 1, "finished_at": None, "points": 0}
    connection = FakeConnection(None)

    def execute(query, params):
        state.queries.append((query, params))
        row = [state.location, state.game, {"attempts": 1}][len(state.queries) - 1]
        return SimpleNamespace(fetchone=lambda: row)

    monkeypatch.setattr(connection, "execute", execute)
    monkeypatch.setattr(game_session, "get_connection", connection)
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
    assert api.queries[0][1][1] == api.student and api.queries[1][1][-2:] == (api.student, 1)
    assert api.queries[1][1][2] == (10 if correct else 0)


@pytest.mark.parametrize("error,status", [(InvalidPhoto("Please retake the photo."), 422),
                                         (OCRUnavailable("private model details"), 503)])
def test_ocr_errors_are_safe_and_do_not_write(api, monkeypatch, error, status):
    def fail(photo):
        raise error
    monkeypatch.setattr(answer_check, "extract_room_numbers", fail)
    response = api.submit()
    assert response.status_code == status and "private" not in response.text
    assert len(api.queries) == 1


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
