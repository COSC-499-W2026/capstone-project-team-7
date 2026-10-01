import psycopg
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Lost In Translation API")


@app.get("/api/health")
def health():
    """Check the API and its PostgreSQL connection."""
    try:
        # Psycopg reads the PG* environment variables supplied by Compose.
        with psycopg.connect(connect_timeout=3) as connection:
            connection.execute("SELECT 1")
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return {"status": "ok", "database": "connected"}
