"""Compose spoken clues using the shared difficulty rules."""

from difficulties import Difficulty, get_clue_rules


def clue_text(number_text: str, description_text: str, difficulty: Difficulty | str) -> str:
    """Include only the content required by this level, rejecting missing content."""
    rules = get_clue_rules(difficulty)
    parts = []
    for required, text in ((rules.include_number, number_text),
                           (rules.include_description, description_text)):
        if required:
            if not text or not text.strip():
                raise ValueError("Required clue text is missing")
            parts.append(text.strip())
    return ". ".join(parts)
