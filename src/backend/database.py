"""PostgreSQL connections shared by backend services."""

import os

import psycopg
from dotenv import find_dotenv, load_dotenv
from psycopg.rows import dict_row

# Walk up from this file to find the repo .env; in Docker there is none and compose supplies settings.
# Existing environment variables, including CI settings, take precedence.
load_dotenv(find_dotenv())


def get_connection():
    """Use as a context manager: commit on success, roll back on failure."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Copy .env.example to .env.")
    # Return rows as dictionaries so callers can use column names instead of positions.
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=5)
