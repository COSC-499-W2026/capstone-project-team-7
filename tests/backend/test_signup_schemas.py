import pytest
from pydantic import ValidationError

from schemas import StudentSignupRequest


@pytest.fixture
def signup():
    return {
        "email": "student@example.com",
        "password": "MysecretPassword123",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "student_number": "00123456",
        "username": "ada",
    }


def test_valid_signup_normalizes_profile_but_preserves_password(signup):
    signup.update(first_name=" Ada ", last_name=" Lovelace ", username=" ada ",
                  student_number=" 00123456 ", email=" student@EXAMPLE.COM ",
                  password=" password with spaces ")
    request = StudentSignupRequest(**signup)
    assert request.model_dump() == {
        **signup, "first_name": "Ada", "last_name": "Lovelace", "username": "ada",
        "student_number": "00123456", "email": "student@example.com",
    }
    assert signup["password"] not in repr(request)


@pytest.mark.parametrize("field", [
    "email", "password", "first_name", "last_name", "student_number", "username",
])
@pytest.mark.parametrize("invalid", ["missing", None, "", "   ", 123])
def test_required_fields_reject_missing_blank_and_non_string_values(signup, field, invalid):
    if invalid == "missing":
        signup.pop(field)
    else:
        signup[field] = invalid
    with pytest.raises(ValidationError) as error:
        StudentSignupRequest(**signup)
    assert error.value.errors()[0]["loc"] == (field,)


@pytest.mark.parametrize("email", [
    "student", "student@", "@example.com", "student@example", "a b@example.com",
])
def test_invalid_email_is_rejected(signup, email):
    signup["email"] = email
    with pytest.raises(ValidationError):
        StudentSignupRequest(**signup)


@pytest.mark.parametrize("field, value", [
    ("password", "a" * 7), ("password", " " * 8),
    ("password", "a" * 73), ("password", "é" * 37),
    ("username", "u" * 51), ("student_number", "1" * 31),
])
def test_field_limits_are_enforced(signup, field, value):
    signup[field] = value
    with pytest.raises(ValidationError):
        StudentSignupRequest(**signup)


@pytest.mark.parametrize("password", ["a" * 8, "a" * 72, "é" * 36])
def test_password_boundaries_are_accepted(signup, password):
    signup.update(password=password, username="u" * 50, student_number="1" * 30)
    assert StudentSignupRequest(**signup).password == password


def test_client_cannot_supply_role(signup):
    with pytest.raises(ValidationError) as error:
        StudentSignupRequest(**signup, role="admin")
    assert error.value.errors()[0]["type"] == "extra_forbidden"
