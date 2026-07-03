from fastapi.testclient import TestClient


def test_register_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "user1@example.com", "password": "strongpassword123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user1@example.com"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_user(client: TestClient) -> None:
    payload = {"email": "duplicate@example.com", "password": "strongpassword123"}

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_login_success(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "login_user@example.com", "password": "strongpassword123"},
    )

    response = client.post(
        "/auth/login",
        data={"username": "login_user@example.com", "password": "strongpassword123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "strongpassword123"},
    )

    response = client.post(
        "/auth/login",
        data={"username": "wrongpass@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
