from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Глобальные настройки приложения, читаются из переменных окружения / .env"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Приложение
    APP_NAME: str = "ml-inference-service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # База данных
    DATABASE_URL: str = "postgresql://ml_user:ml_password@db:5432/ml_inference"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ML
    MODEL_DIR: str = "models"
    CATEGORY_MODEL_PATH: str = "models/category_model.pkl"
    LEVEL_MODEL_PATH: str = "models/level_model.pkl"
    VECTORIZER_PATH: str = "models/vectorizer.pkl"

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Cache
    PREDICTION_CACHE_TTL_SECONDS: int = 86400


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
