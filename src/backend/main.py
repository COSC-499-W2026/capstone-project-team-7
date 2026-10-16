import logging

import psycopg
from fastapi import FastAPI, HTTPException

from admin import router as admin_router
from admin_creation import router as admin_creation_router
from auth import router as auth_router
from class_enrollment import router as class_enrollment_router
from database import get_connection
from password_change import router as password_change_router
from student_signup import router as student_signup_router
from teacher_signup import router as teacher_signup_router
from teacher_approval import router as teacher_approval_router
from teacher_access import router as teacher_access_router
from student_deletion import router as student_deletion_router
from teacher_deletion import router as teacher_deletion_router

app = FastAPI()
app.include_router(teacher_signup_router)
app.include_router(auth_router)
app.include_router(password_change_router)
app.include_router(student_signup_router)
app.include_router(teacher_approval_router)
app.include_router(admin_router)
app.include_router(admin_creation_router)
app.include_router(teacher_access_router)
app.include_router(student_deletion_router)
app.include_router(teacher_deletion_router)
app.include_router(class_enrollment_router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello World"}


@app.get("/api/health/db")
def database_health():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, RuntimeError):
        logging.getLogger(__name__).warning("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok"}
