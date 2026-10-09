import logging

import psycopg
from fastapi import FastAPI, HTTPException

from auth import router as auth_router
from database import get_connection
from teacher_signup import router as teacher_signup_router

app = FastAPI()
app.include_router(teacher_signup_router)
app.include_router(auth_router)


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
