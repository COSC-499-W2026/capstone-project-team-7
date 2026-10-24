from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

import game_session
from main import app
from utils import answer_check
from utils.ocr import InvalidPhoto, OCRUnavailable


@pytest.fixture
def api(monkeypatch):
    state = SimpleNamespace(queries=[], error_at=None, candidates=["LIB 308"], student=uuid4(), rolled_back=False)
    state.location = {"building": "LIB", "room_number": "308", "current_position": 1, "finished_at": None}
    state.game = {"current_position": 2, "finished_at": None, "points": 10}
    state.spot = {"attempts": 1}

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, kind, *args):
            state.rolled_back = kind is not None
            if state.error_at == "commit":
                raise psycopg.OperationalError("private database details")

        def execute(self, query, params):
            step = len(state.queries)
            state.queries.append((query, params))
            if state.error_at == step:
                raise psycopg.OperationalError("private database details")
            return SimpleNamespace(fetchone=lambda: [state.location, state.game, state.spot][step])

    monkeypatch.setattr(game_session, "get_connection", Connection)
    monkeypatch.setattr(answer_check, "extract_room_numbers", lambda photo: state.candidates)
    app.dependency_overrides[game_session.require_student] = lambda: {"id": state.student, "role": "student"}
    with TestClient(app, base_url="https://testserver") as client:
        state.submit = lambda photo=b"photo", game_id=uuid4(): client.post(f"/api/game/{game_id}/answer", content=photo)
        yield state
    app.dependency_overrides.clear()


@pytest.mark.parametrize("building,room", [("LIB", "308"), ("EME", "0050")])
def test_correct_photo_awards_points_for_owned_current_target(api, building, room):
    api.location.update(building=building, room_number=room)
    api.candidates = [f"{building} {room}"]
    response = api.submit()
    assert response.status_code == 200
    assert response.json() == {"correct": True, "attempts": 1, "finished": False, "next_position": 2,
                               "points_awarded": 10, "total_points": 10, "message": "Correct room!"}
    assert api.queries[0][1][1] == api.student
    assert api.queries[1][1][2] == 10 and api.queries[1][1][-2:] == (api.student, 1)


@pytest.mark.parametrize("candidates", [[], ["LIB 309"], ["SCI 308"], ["LIB 0308"]])
def test_wrong_or_unreadable_photo_awards_nothing_and_stays_on_target(api, candidates):
    api.candidates = candidates
    api.game.update(current_position=1, points=20)
    body = api.submit().json()
    assert body["correct"] is False and body["points_awarded"] == 0 and body["total_points"] == 20
    assert body["next_position"] is None and "retake" in body["message"]
    assert api.queries[1][1][0] == api.queries[1][1][2] == 0


@pytest.mark.parametrize("field,row,status", [("location", None, 404), ("game", None, 409), ("spot", None, 409)])
def test_missing_or_concurrently_completed_target_cannot_award_points(api, field, row, status):
    setattr(api, field, row)
    assert api.submit().status_code == status
    assert api.rolled_back == (field != "location")


def test_final_photo_finishes_game(api):
    api.location["current_position"] = 5
    api.game.update(current_position=5, finished_at="now", points=50)
    body = api.submit().json()
    assert body["finished"] and body["next_position"] is None and body["total_points"] == 50


@pytest.mark.parametrize("finished", [True, False])
def test_finished_game_or_bad_uuid_does_not_run_ocr(api, finished):
    api.location["finished_at"] = "now" if finished else None
    assert api.submit(game_id=uuid4() if finished else "invalid").status_code == (409 if finished else 422)


@pytest.mark.parametrize("error,status", [(InvalidPhoto("Please retake the photo."), 422),
                                         (OCRUnavailable("private model details"), 503)])
def test_ocr_errors_are_safe_and_do_not_write(api, monkeypatch, error, status):
    def fail(photo):
        raise error
    monkeypatch.setattr(answer_check, "extract_room_numbers", fail)
    response = api.submit()
    assert response.status_code == status and "private" not in response.text
    assert len(api.queries) == 1


@pytest.mark.parametrize("stage", [0, 1, 2, "commit"])
def test_database_errors_are_safe(api, stage):
    api.error_at = stage
    response = api.submit()
    assert response.status_code == 503 and response.json() == {"detail": "Database unavailable"}


@pytest.mark.parametrize("photo", [b"", b"123456"])
def test_empty_or_oversized_photo_does_not_reach_database(api, monkeypatch, photo):
    monkeypatch.setattr(game_session, "MAX_PHOTO_BYTES", 5)
    assert api.submit(photo=photo).status_code == (422 if not photo else 413)
    assert api.queries == []


@pytest.mark.parametrize("role,status", [(None, 401), ("teacher", 403), ("admin", 403)])
def test_photo_verification_requires_student_session(api, role, status):
    from auth import current_user
    app.dependency_overrides.pop(game_session.require_student)
    if role:
        app.dependency_overrides[current_user] = lambda: {"id": api.student, "role": role}
    assert api.submit().status_code == status and api.queries == []
