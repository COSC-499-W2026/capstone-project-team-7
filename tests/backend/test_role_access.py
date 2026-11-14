from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import admin
import auth
import student_enrollment
import teacher_access
from main import app

client = TestClient(app)


@pytest.mark.parametrize("role", ["student", "teacher", "admin"])
def test_matching_role_is_let_through(role):
    user = {"id": uuid4(), "role": role}
    assert auth.require_role(role)(user) is user


@pytest.mark.parametrize("role, other", [("student", "teacher"), ("teacher", "admin"), ("admin", "student")])
def test_other_roles_are_refused(role, other):
    with pytest.raises(auth.HTTPException) as refused:
        auth.require_role(role)({"id": uuid4(), "role": other})
    assert refused.value.status_code == 403
    assert refused.value.detail == f"{role.capitalize()} access required"


def test_features_share_the_auth_role_checks():
    # Routes and test overrides rely on these being the same dependency objects.
    assert admin.require_admin is auth.require_admin
    assert teacher_access.require_teacher is auth.require_teacher
    assert student_enrollment.require_student is auth.require_student


@pytest.mark.parametrize("role", ["student", "teacher"])
def test_admin_routes_refuse_other_roles(role):
    app.dependency_overrides[auth.current_user] = lambda: {"id": uuid4(), "role": role}
    try:
        response = client.patch(f"/api/admin/classes/{uuid4()}/teacher", json={"teacher_email": "t@example.com"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required"}
