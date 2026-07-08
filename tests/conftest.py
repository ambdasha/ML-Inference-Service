import os

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL", "postgresql://ml_user:ml_password@localhost:5435/ml_inference_test"
)

from app import main  # noqa: E402
from app.core import cache  # noqa: E402
from app.db.database import Base, get_db  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]



@pytest.fixture()
def mock_ml(monkeypatch):
    """Подменяет ML-модель в тестах /match."""

    from app.api import match as match_api

    class DummyModelBundle:
        version = "test-model-v1"

    def fake_get_model_bundle(*args, **kwargs):
        return DummyModelBundle()

    def fake_predict(text: str, *args, **kwargs):
        lower_text = text.lower()

        if "frontend" in lower_text or "react" in lower_text or "javascript" in lower_text:
            return {
                "category": "frontend",
                "level": "junior",
                "skills": ["javascript", "react"],
                "confidence": 0.9,
            }

        return {
            "category": "backend",
            "level": "junior",
            "skills": ["python", "fastapi", "postgresql", "redis", "docker", "rest api"],
            "confidence": 0.9,
        }

    class FakePredictor:
        def predict(self, text: str, *args, **kwargs):
            return fake_predict(text, *args, **kwargs)

    monkeypatch.setattr(match_api, "get_model_bundle", fake_get_model_bundle)
    monkeypatch.setattr(match_api, "get_predictor", lambda: FakePredictor())

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def fake_redis(monkeypatch):
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache, "redis_client", fake)
    monkeypatch.setattr("app.api.deps.check_rate_limit", cache.check_rate_limit)
    return fake


@pytest.fixture()
def client(db_session, fake_redis, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    main.app.dependency_overrides[get_db] = override_get_db

    # Подменяем ML-модель на детерминированный мок, чтобы тесты
    # не зависели от обученных артефактов models/*.pkl
    from app.ml import model_loader

    class FakeBundle:
        version = "test-v1"

    class FakePredictor:
        def predict(self, text: str) -> dict:
            return {
                "category": "backend",
                "level": "junior",
                "skills": ["Python", "PostgreSQL"],
                "confidence": 0.9,
            }

    monkeypatch.setattr(model_loader, "get_model_bundle", lambda: FakeBundle())
    monkeypatch.setattr("app.api.predict.get_model_bundle", lambda: FakeBundle())
    monkeypatch.setattr("app.api.predict.get_predictor", lambda: FakePredictor())

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Регистрирует пользователя и возвращает заголовки с Bearer-токеном."""
    email = "predict_user@example.com"
    password = "strongpassword123"

    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

