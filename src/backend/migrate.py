"""Apply versioned SQL migrations: python src/backend/migrate.py."""

from hashlib import sha256
from pathlib import Path

from database import get_connection

MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def apply_migrations(connection, directory=MIGRATIONS_DIR):
    """Serialize runners and apply all pending files in one transaction."""
    applied = []
    # Roll back the entire batch if a migration fails.
    with connection.transaction():
        # Only one migration runner can proceed at a time; commit/rollback releases the lock.
        connection.execute("SELECT pg_advisory_xact_lock(499007)")
        # Track completed files so subsequent runs can safely skip them.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        # Numbered filenames determine the order: 001, 002, 003, and so on.
        for path in sorted(directory.glob("*.sql")):
            content = path.read_text(encoding="utf-8")
            checksum = sha256(content.encode("utf-8")).hexdigest()
            previous = connection.execute(
                "SELECT checksum FROM schema_migrations WHERE version = %s",
                (path.name,),
            ).fetchone()
            if previous:
                # Editing an applied file would make databases disagree; add a new file instead.
                if previous["checksum"] != checksum:
                    raise RuntimeError(
                        f"Applied migration {path.name} changed; add a new migration instead."
                    )
                continue
            connection.execute(content)
            # Record success in the same transaction as the schema change.
            connection.execute(
                "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                (path.name, checksum),
            )
            applied.append(path.name)
    return applied


if __name__ == "__main__":
    with get_connection() as connection:
        applied = apply_migrations(connection)
    print("Applied: " + ", ".join(applied) if applied else "Database is up to date.")
