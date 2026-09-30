from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_hello_returns_message():
    response = client.get("/api/hello")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_unknown_route_returns_404():
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
