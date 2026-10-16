"""Request validation for student signup; persistence belongs to the service."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StudentSignupRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)

    email: EmailStr
    password: str = Field(min_length=8, repr=False)
    first_name: RequiredText
    last_name: RequiredText
    student_number: Annotated[RequiredText, Field(max_length=30)]
    username: Annotated[RequiredText, Field(max_length=50)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Password must not be blank")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value
