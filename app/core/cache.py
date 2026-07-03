import hashlib
import json

import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def make_prediction_cache_key(text: str, model_version: str) -> str:
    """Формирует ключ кэша: hash(text + model_version) -> prediction_result."""
    raw = f"{model_version}:{text.strip().lower()}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"prediction_cache:{digest}"


def get_cached_prediction(text: str, model_version: str) -> dict | None:
    key = make_prediction_cache_key(text, model_version)
    cached = redis_client.get(key)
    if cached is None:
        return None
    return json.loads(cached)


def set_cached_prediction(text: str, model_version: str, result: dict) -> None:
    key = make_prediction_cache_key(text, model_version)
    redis_client.set(key, json.dumps(result), ex=settings.PREDICTION_CACHE_TTL_SECONDS)


def check_rate_limit(identifier: str) -> bool:
    """Простой rate limiter с фиксированным окном на базе Redis.

    Возвращает True, если запрос разрешён, False — если лимит превышен.
    """
    key = f"rate_limit:{identifier}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

    return current <= settings.RATE_LIMIT_REQUESTS
