"""Points for completing a location at each game difficulty."""

import logging

from difficulties import Difficulty

_POINTS = {Difficulty.BASIC: 10, Difficulty.ADVANCED: 20, Difficulty.EXPERT: 30}


def points_for_difficulty(difficulty: Difficulty | str) -> int:
    """Return completion points, logging and rejecting unsupported difficulties."""
    try:
        level = Difficulty(difficulty)
    except ValueError:
        logging.getLogger(__name__).error("Cannot calculate points: unsupported game difficulty")
        raise ValueError("Unsupported game difficulty") from None
    return _POINTS[level]
