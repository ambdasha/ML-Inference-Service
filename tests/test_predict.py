from fastapi.testclient import TestClient


def test_predict_requires_auth(client: TestClient) -> None:
    response = client.post("/predict", json={"text": "Ищем backend-разработчика на Python"})
    assert response.status_code == 401


def test_predict_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/predict",
        json={"text": "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "backend"
    assert data["level"] == "junior"
    assert "Python" in data["skills"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["cached"] is False


def test_predict_cache_hit(client: TestClient, auth_headers: dict[str, str]) -> None:
    text = "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."

    first = client.post("/predict", json={"text": text}, headers=auth_headers)
    assert first.json()["cached"] is False

    second = client.post("/predict", json={"text": text}, headers=auth_headers)
    assert second.json()["cached"] is True


def test_predict_validation_error(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post("/predict", json={"text": "short"}, headers=auth_headers)
    assert response.status_code == 422


def test_predict_batch(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/predict/batch",
        json=[
            {"text": "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."},
            {"text": "Требуется backend-инженер. Go, Kafka, PostgreSQL, Docker."},
        ],
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for item in data:
        assert item["category"] == "backend"


def test_feedback_submission(client: TestClient, auth_headers: dict[str, str]) -> None:
    client.post(
        "/predict",
        json={"text": "Ищем backend-разработчика на Python. PostgreSQL, Redis, Docker."},
        headers=auth_headers,
    )

    history_response = client.get("/history", headers=auth_headers)
    prediction_id = history_response.json()["items"][0]["id"]

    feedback_response = client.post(
        f"/predictions/{prediction_id}/feedback",
        json={"correct_category": "data_science", "correct_level": "middle"},
        headers=auth_headers,
    )

    assert feedback_response.status_code == 204


def test_feedback_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/predictions/{fake_id}/feedback",
        json={"correct_category": "backend"},
        headers=auth_headers,
    )
    assert response.status_code == 404
