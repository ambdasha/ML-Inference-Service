import os

import joblib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelBundle:
    """Контейнер для загруженных артефактов модели: векторизатор + классификаторы."""

    def __init__(self, vectorizer, category_model, level_model, version: str = "v1") -> None:
        self.vectorizer = vectorizer
        self.category_model = category_model
        self.level_model = level_model
        self.version = version


_model_bundle: ModelBundle | None = None


def load_models(force_reload: bool = False) -> ModelBundle:
    """Загружает модели в память (один раз, singleton). Бросает FileNotFoundError, если артефактов нет."""
    global _model_bundle

    if _model_bundle is not None and not force_reload:
        return _model_bundle

    for path in (settings.VECTORIZER_PATH, settings.CATEGORY_MODEL_PATH, settings.LEVEL_MODEL_PATH):
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Файл модели не найден: {path}. "
                f"Запустите обучение: python training/train.py"
            )

    vectorizer = joblib.load(settings.VECTORIZER_PATH)
    category_model = joblib.load(settings.CATEGORY_MODEL_PATH)
    level_model = joblib.load(settings.LEVEL_MODEL_PATH)

    logger.info("ML-модели успешно загружены из %s", settings.MODEL_DIR)

    _model_bundle = ModelBundle(vectorizer, category_model, level_model)
    return _model_bundle


def get_model_bundle() -> ModelBundle:
    return load_models()
