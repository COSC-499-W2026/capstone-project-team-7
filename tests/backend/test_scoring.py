import logging

import pytest

from difficulties import Difficulty
from utils.scoring import points_for_attempt, points_for_difficulty


@pytest.mark.parametrize("difficulty,points", [("basic", 10), ("advanced", 20), ("expert", 30)])
def test_difficulty_completion_points(difficulty, points):
    assert points_for_difficulty(difficulty) == points
    assert points_for_difficulty(Difficulty(difficulty)) == points


@pytest.mark.parametrize("difficulty", ["easy", "Basic", " basic ", "", None, 1, True])
def test_invalid_difficulty_is_rejected_and_logged(difficulty, caplog):
    with caplog.at_level(logging.ERROR), pytest.raises(ValueError, match="Unsupported game difficulty"):
        points_for_difficulty(difficulty)
    assert any(record.name == "utils.scoring" and record.levelno == logging.ERROR for record in caplog.records)


@pytest.mark.parametrize("completion_points,expected", [(10, [10, 6, 3, 3]),
                                                       (20, [20, 12, 6, 6]),
                                                       (30, [30, 18, 9, 9])])
def test_attempt_completion_points(completion_points, expected):
    assert [points_for_attempt(completion_points, attempt) for attempt in (1, 2, 3, 10)] == expected


@pytest.mark.parametrize("attempt", [0, -1])
def test_non_positive_attempt_is_rejected(attempt):
    with pytest.raises(ValueError, match="Attempt must be positive"):
        points_for_attempt(10, attempt)
