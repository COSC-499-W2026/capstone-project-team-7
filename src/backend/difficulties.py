"""Shared difficulty values and rules for the content of a hunt clue."""

from dataclasses import dataclass
from enum import Enum


class Difficulty(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass(frozen=True)
class ClueRules:
    include_number: bool
    include_description: bool


_CLUE_RULES = {
    Difficulty.BASIC: ClueRules(include_number=True, include_description=False),
    Difficulty.ADVANCED: ClueRules(include_number=True, include_description=True),
    Difficulty.EXPERT: ClueRules(include_number=False, include_description=True),
}


def get_clue_rules(difficulty: Difficulty | str) -> ClueRules:
    """Return clue content rules, rejecting unsupported difficulty values."""
    return _CLUE_RULES[Difficulty(difficulty)]
