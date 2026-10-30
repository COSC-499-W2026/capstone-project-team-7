import logging

import pytest

from difficulties import Difficulty
from utils.scoring import points_for_difficulty


@pytest.mark.parametrize("difficulty,points", [("basic", 10), ("advanced", 20), ("expert", 30)])
def test_difficulty_completion_points(difficulty, points):
    assert points_for_difficulty(difficulty) == points
    assert points_for_difficulty(Difficulty(difficulty)) == points


@pytest.mark.parametrize("difficulty", ["easy", "Basic", " basic ", "", None, 1, True])
def test_invalid_difficulty_is_rejected_and_logged(difficulty, caplog):
    with caplog.at_level(logging.ERROR), pytest.raises(ValueError, match="Unsupported game difficulty"):
        points_for_difficulty(difficulty)
    assert any(record.name == "utils.scoring" and record.levelno == logging.ERROR for record in caplog.records)
