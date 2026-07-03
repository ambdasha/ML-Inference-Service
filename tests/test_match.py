import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("mock_ml")


def test_match_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/match",
        json={
            "resume_text": "Python backend developer with FastAPI, PostgreSQL and Docker.",
            "vacancy_text": "Looking for backend developer with Python, FastAPI and Redis.",
        },
    )

    assert response.status_code == 401


def test_match_success(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/match",
        json={
            "resume_text": (
                "Backend developer. Python, FastAPI, PostgreSQL, Redis, Docker. "
                "Worked with REST API and authentication."
            ),
            "vacancy_text": (
                "Looking for junior backend developer. Python, FastAPI, PostgreSQL, "
                "Redis, Docker, REST API."
            ),
        },
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert 0.0 <= data["match_score"] <= 1.0
    assert isinstance(data["category_match"], bool)
    assert isinstance(data["level_match"], bool)

    assert "matched_skills" in data
    assert "missing_skills" in data
    assert "extra_resume_skills" in data

    assert data["resume_analysis"]["category"] == "backend"
    assert data["vacancy_analysis"]["category"] == "backend"

    assert data["explanation"]


def test_match_rejects_short_text(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/match",
        json={
            "resume_text": "short",
            "vacancy_text": "Looking for backend developer with Python and PostgreSQL.",
        },
        headers=auth_headers,
    )

    assert response.status_code == 422