import pytest

from utils.clue_text import clue_text

NUMBER = "trois cent seize"
DESCRIPTION = "Près de la bibliothèque."


@pytest.mark.parametrize("difficulty,expected", [
    ("basic", NUMBER),
    ("advanced", f"{NUMBER}. {DESCRIPTION}"),
    ("expert", DESCRIPTION),
])
def test_clue_contains_exactly_the_required_content(difficulty, expected):
    assert clue_text(NUMBER, DESCRIPTION, difficulty) == expected


@pytest.mark.parametrize("difficulty,number,description", [
    ("basic", "", DESCRIPTION),
    ("basic", "   ", DESCRIPTION),
    ("advanced", "", DESCRIPTION),
    ("advanced", NUMBER, ""),
    ("expert", NUMBER, "   "),
])
def test_missing_required_content_is_rejected(difficulty, number, description):
    with pytest.raises(ValueError, match="Required clue text is missing"):
        clue_text(number, description, difficulty)


def test_unused_content_is_not_required():
    assert clue_text(NUMBER, "", "basic") == NUMBER
    assert clue_text("", DESCRIPTION, "expert") == DESCRIPTION


def test_content_is_trimmed():
    assert clue_text(f" {NUMBER} ", f" {DESCRIPTION} ", "advanced") == f"{NUMBER}. {DESCRIPTION}"


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        clue_text(NUMBER, DESCRIPTION, "easy")
