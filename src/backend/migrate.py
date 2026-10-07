"""Apply versioned SQL files with: python src/backend/migrate.py."""

import os
from hashlib import sha256
from pathlib import Path

import psycopg
from dotenv import find_dotenv, load_dotenv

MIGRATIONS_DIR = Path(__file__).with_name('migrations')


def apply_migrations(connection, directory=MIGRATIONS_DIR):
    """Apply a batch atomically; reject changes to previously applied files."""
    applied = []
    with connection.transaction():
        connection.execute('SELECT pg_advisory_xact_lock(499007)')
        connection.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                checksum TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        ''')
        for path in sorted(directory.glob('*.sql')):
            content = path.read_text(encoding='utf-8')
            checksum = sha256(content.encode('utf-8')).hexdigest()
            previous = connection.execute(
                'SELECT checksum FROM schema_migrations WHERE version = %s', (path.name,)
            ).fetchone()
            if previous:
                if previous[0] != checksum:
                    raise RuntimeError(f'Applied migration {path.name} changed; add a new migration.')
                continue
            connection.execute(content)
            connection.execute(
                'INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)',
                (path.name, checksum),
            )
            applied.append(path.name)
    return applied


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    url = os.getenv('DATABASE_URL')
    if not url:
        raise SystemExit('Set DATABASE_URL or configure it in the repository .env file.')
    with psycopg.connect(url, connect_timeout=5) as connection:
        applied = apply_migrations(connection)
    print('Applied: ' + ', '.join(applied) if applied else 'Database is up to date.')
