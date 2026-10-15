"""Student signup API backed by the shared schema and registration service."""

import logging
from typing import Literal
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from registration import DuplicateStudentAccount, create_student
from schemas import StudentSignupRequest

router = APIRouter(prefix="/api/auth/student", tags=["Student registration"])


class StudentSignupResponse(BaseModel):
    id: UUID
    role: Literal["student"]


@router.post("/signup", status_code=201, response_model=StudentSignupResponse,
             summary="Create a student account", responses={
                 409: {"description": "Account details already in use"},
                 503: {"description": "Database unavailable"},
             })
def signup_student(info: StudentSignupRequest):
    try:
        return create_student(**info.model_dump())
    except DuplicateStudentAccount:
        raise HTTPException(status_code=409, detail="Account details already in use") from None
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Student signup database operation failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
