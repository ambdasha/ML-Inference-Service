from fastapi.testclient import TestClient


def test_history_empty(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/history", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_history_after_predict(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(
        "/predict",
        json={"text": "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."},
        headers=auth_headers,
    )
    client.post(
        "/predict",
        json={"text": "Требуется backend-инженер. Go, Kafka, PostgreSQL, Docker."},
        headers=auth_headers,
    )

    response = client.get("/history", headers=auth_headers)
    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["category"] == "backend"


def test_history_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(3):
        client.post(
            "/predict",
            json={"text": f"Ищем backend-разработчика на Python номер {i}. PostgreSQL, Redis."},
            headers=auth_headers,
        )

    response = client.get("/history", params={"limit": 2, "offset": 0}, headers=auth_headers)
    data = response.json()

    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_history_item_by_id(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(
        "/predict",
        json={"text": "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."},
        headers=auth_headers,
    )

    history = client.get("/history", headers=auth_headers).json()
    item_id = history["items"][0]["id"]

    response = client.get(f"/history/{item_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_history_item_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/history/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_history_requires_auth(client: TestClient) -> None:
    response = client.get("/history")
    assert response.status_code == 401
