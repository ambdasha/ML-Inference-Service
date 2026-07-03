import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_current_user, parse_uuid
from app.core.cache import get_cached_prediction, set_cached_prediction
from app.core.logging import get_logger
from app.core.metrics import (
    cache_hits,
    cache_misses,
    model_confidence,
    prediction_count,
    prediction_errors,
    prediction_latency,
)
from app.db.database import get_db
from app.db.models import User
from app.db.repositories import FeedbackRepository, PredictionRepository
from app.ml.model_loader import get_model_bundle
from app.ml.predictor import get_predictor
from app.schemas.prediction import FeedbackRequest, PredictRequest, PredictResponse

router = APIRouter(tags=["predict"])
logger = get_logger(__name__)


def _run_prediction(text: str) -> tuple[dict, bool]:
    """Выполняет предсказание с использованием кэша. Возвращает (результат, cached)."""
    bundle = get_model_bundle()
    cached_result = get_cached_prediction(text, bundle.version)

    if cached_result is not None:
        cache_hits.inc()
        return cached_result, True

    cache_misses.inc()
    start = time.perf_counter()

    try:
        predictor = get_predictor()
        result = predictor.predict(text)
    except Exception:
        prediction_errors.inc()
        raise

    elapsed = time.perf_counter() - start
    prediction_latency.observe(elapsed)
    model_confidence.observe(result["confidence"])
    prediction_count.labels(category=result["category"], level=result["level"]).inc()

    set_cached_prediction(text, bundle.version, result)
    return result, False


@router.post("/predict", response_model=PredictResponse, dependencies=[Depends(enforce_rate_limit)])
def predict(
    payload: PredictRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PredictResponse:
    result, cached = _run_prediction(payload.text)

    PredictionRepository(db).create(
        user_id=current_user.id,
        input_text=payload.text,
        category=result["category"],
        level=result["level"],
        skills=result["skills"],
        confidence=result["confidence"],
        cached=cached,
        model_version=get_model_bundle().version,
    )

    return PredictResponse(**result, cached=cached)


@router.post(
    "/predict/batch",
    response_model=list[PredictResponse],
    dependencies=[Depends(enforce_rate_limit)],
)
def predict_batch(
    payloads: list[PredictRequest],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PredictResponse]:
    """Пакетное предсказание для нескольких текстов (синхронно).

    Для больших объёмов (сотни текстов) рекомендуется выносить обработку
    в фоновую задачу (Celery) и отдавать job_id через GET /jobs/{id}.
    """
    if not payloads:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пустой список запросов")

    repo = PredictionRepository(db)
    responses: list[PredictResponse] = []

    for item in payloads:
        result, cached = _run_prediction(item.text)
        repo.create(
            user_id=current_user.id,
            input_text=item.text,
            category=result["category"],
            level=result["level"],
            skills=result["skills"],
            confidence=result["confidence"],
            cached=cached,
            model_version=get_model_bundle().version,
        )
        responses.append(PredictResponse(**result, cached=cached))

    return responses


@router.post("/predictions/{prediction_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
def submit_feedback(
    prediction_id: str,
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Позволяет пользователю исправить предсказание модели (для дообучения)."""
    pred_uuid = parse_uuid(prediction_id)

    prediction = PredictionRepository(db).get_by_id(pred_uuid, current_user.id)
    if prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Предсказание не найдено")

    FeedbackRepository(db).upsert(
        prediction_id=prediction.id,
        correct_category=payload.correct_category.value if payload.correct_category else None,
        correct_level=payload.correct_level.value if payload.correct_level else None,
        comment=payload.comment,
    )
