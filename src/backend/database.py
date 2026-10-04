"""PostgreSQL connections shared by the API and migration command."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Find .env even when the backend is launched from a different working directory.
# Existing environment variables, including CI settings, take precedence.
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    """Use as a context manager: commit on success, roll back on failure."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Copy .env.example to .env.")
    # Return rows as dictionaries so callers can use column names instead of positions.
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5)
