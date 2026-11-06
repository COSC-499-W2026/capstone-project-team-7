"""Create the initial admin account with: cd src/backend && python -m utils.seed_admin.

Reads ADMIN_EMAIL and ADMIN_PASSWORD (optionally ADMIN_USERNAME) from the environment or .env.
Safe to run more than once: nothing is created if an admin already exists.
"""

import os

from auth import MAX_PASSWORD_BYTES
from database import get_connection
from utils.passwords import hash_password


def seed_admin(connection, email, password, username='admin'):
    """Return True if the admin was created, False if an admin already exists."""
    if len(password.encode('utf-8')) > MAX_PASSWORD_BYTES:
        raise ValueError(f'Admin password must be at most {MAX_PASSWORD_BYTES} bytes.')
    with connection.transaction():
        # Serialize concurrent runs so two admins cannot be created at the same time.
        connection.execute('SELECT pg_advisory_xact_lock(499039)')
        if connection.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1").fetchone():
            return False
        connection.execute('''
            INSERT INTO users (email, username, password, first_name, last_name, role)
            VALUES (%s, %s, %s, 'System', 'Admin', 'admin')
        ''', (email.strip(), username, hash_password(password)))
    return True


if __name__ == '__main__':
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    if not email or not password:
        raise SystemExit('Set ADMIN_EMAIL and ADMIN_PASSWORD in the environment or .env.')
    with get_connection() as connection:
        created = seed_admin(connection, email, password, os.getenv('ADMIN_USERNAME', 'admin'))
    print(f'Created admin account {email.strip()}.' if created else 'Admin already exists; nothing created.')
