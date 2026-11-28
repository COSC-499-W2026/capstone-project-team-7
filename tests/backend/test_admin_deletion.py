from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

import admin_deletion
from database import get_connection
from main import app
from test_teacher_access import PASSWORD, access_db, client, login

URL = "/api/admin/admins"


def account_id(username):
    with get_connection() as connection:
        return connection.execute("SELECT id FROM users WHERE username = %s", (username,)).fetchone()["id"]


def create_second_admin(client):
    response = client.post(URL, json={
        "email": "other@example.com", "username": "other", "password": PASSWORD,
        "first_name": "Other", "last_name": "Admin",
    })
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_admin_can_list_and_delete_another_admin(access_db, client):
    login(client, "admin")
    target = create_second_admin(client)
    assert client.get(URL).json() == [{"id": target, "username": "other", "email": "other@example.com"}]
    with TestClient(app, base_url="https://testserver") as other:
        login(other, "other")
        assert client.delete(f"{URL}/{target}").status_code == 204
        assert other.get("/api/auth/me").status_code == 401
    assert client.get(URL).json() == []
    assert client.delete(f"{URL}/{target}").status_code == 404
    with get_connection() as connection:
        assert connection.execute("SELECT id FROM users WHERE id = %s", (target,)).fetchone() is None


@pytest.mark.parametrize("second_admin", [True, False], ids=["self", "last"])
def test_refuses_self_or_last_admin_deletion(access_db, client, second_admin):
    login(client, "admin")
    if second_admin:
        create_second_admin(client)
    own_id = account_id("admin")
    response = client.delete(f"{URL}/{own_id}")
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "You cannot delete your own admin account" if second_admin else "The last admin account cannot be deleted"
    )
    assert account_id("admin") == own_id


def test_refuses_to_delete_an_account_with_another_role(access_db, client):
    login(client, "admin")
    teacher = account_id("teacher")
    assert client.delete(f"{URL}/{teacher}").status_code == 404
    assert account_id("teacher") == teacher


@pytest.mark.parametrize("role, status", [(None, 401), ("teacher", 403), ("student", 403)])
def test_admin_account_routes_require_admin_session(access_db, client, role, status):
    if role:
        login(client, role)
    assert client.get(URL).status_code == status
    assert client.delete(f"{URL}/{account_id('admin')}").status_code == status


def test_database_failure_returns_503(access_db, client, monkeypatch):
    login(client, "admin")

    def unavailable():
        raise RuntimeError("Private database details")

    monkeypatch.setattr(admin_deletion, "get_connection", unavailable)
    response = client.delete(f"{URL}/{account_id('admin')}")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert client.get(URL).status_code == 503


def test_two_admins_cannot_delete_each_other_concurrently(access_db, client):
    login(client, "admin")
    target = create_second_admin(client)
    own_id = account_id("admin")
    barrier = Barrier(2)

    def delete(requester, admin_id):
        barrier.wait(timeout=5)
        return requester.delete(f"{URL}/{admin_id}").status_code

    with TestClient(app, base_url="https://testserver") as other, ThreadPoolExecutor(max_workers=2) as pool:
        login(other, "other")
        first = pool.submit(delete, client, target)
        second = pool.submit(delete, other, own_id)
        assert sorted([first.result(), second.result()]) == [204, 401]
    with get_connection() as connection:
        assert connection.execute("SELECT count(*) AS total FROM users WHERE role = 'admin'").fetchone()["total"] == 1
