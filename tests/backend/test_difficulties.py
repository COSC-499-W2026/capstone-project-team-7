from dataclasses import FrozenInstanceError

import pytest
from pydantic import TypeAdapter, ValidationError

from difficulties import Difficulty, get_clue_rules


@pytest.mark.parametrize("value, number, description", [
    ("basic", True, False),
    ("advanced", True, True),
    ("expert", False, True),
])
def test_supported_difficulties_have_expected_clue_content(value, number, description):
    difficulty = Difficulty(value)
    rules = get_clue_rules(difficulty)
    assert rules.include_number is number
    assert rules.include_description is description
    assert get_clue_rules(value) == rules


@pytest.mark.parametrize("value", ["easy", "Basic", " basic ", "", None, 1, True])
def test_unsupported_difficulty_has_no_clue_rules(value):
    with pytest.raises(ValueError):
        get_clue_rules(value)


@pytest.mark.parametrize("value", ["basic", "advanced", "expert"])
def test_difficulty_can_be_validated_and_serialized_with_pydantic(value):
    adapter = TypeAdapter(Difficulty)
    difficulty = adapter.validate_python(value)
    assert difficulty is Difficulty(value)
    assert adapter.dump_json(difficulty) == f'"{value}"'.encode()


@pytest.mark.parametrize("value", ["easy", "Basic", "", None, 1])
def test_pydantic_rejects_unsupported_difficulties(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Difficulty).validate_python(value)


def test_shared_clue_rules_cannot_be_modified():
    rules = get_clue_rules("basic")
    with pytest.raises(FrozenInstanceError):
        rules.include_description = True
