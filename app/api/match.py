import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_current_user
from app.db.database import get_db
from app.db.models import User
from app.db.repositories import MatchHistoryRepository
from app.ml.matcher import (
    build_match_explanation,
    calculate_match_score,
    calculate_skill_match,
)
from app.ml.model_loader import get_model_bundle
from app.ml.predictor import get_predictor
from app.schemas.match import (
    MatchHistoryItem,
    MatchHistoryList,
    MatchRequest,
    MatchResponse,
    TextAnalysisResult,
)

router = APIRouter(prefix="/match", tags=["match"])


def _to_text_analysis_result(result: dict) -> TextAnalysisResult:
    """Преобразует dict результата Predictor в Pydantic-схему."""
    return TextAnalysisResult(
        category=result["category"],
        level=result["level"],
        skills=result["skills"],
        confidence=result["confidence"],
    )


def _build_match_response(
    *,
    resume_result: dict,
    vacancy_result: dict,
    matched_skills: list[str],
    missing_skills: list[str],
    extra_resume_skills: list[str],
    category_match: bool,
    level_match: bool,
    match_score: float,
    explanation: str,
    model_version: str | None,
) -> MatchResponse:
    """Собирает MatchResponse из промежуточных результатов."""
    return MatchResponse(
        match_score=match_score,
        category_match=category_match,
        level_match=level_match,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        extra_resume_skills=extra_resume_skills,
        resume_analysis=_to_text_analysis_result(resume_result),
        vacancy_analysis=_to_text_analysis_result(vacancy_result),
        explanation=explanation,
        model_version=model_version,
    )

@router.post(
    "",
    response_model=MatchResponse,
    dependencies=[Depends(enforce_rate_limit)],
)
def match_resume_with_vacancy(
    payload: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchResponse:
    """Сравнивает резюме кандидата с текстом вакансии и сохраняет результат."""
    bundle = get_model_bundle()
    model_version = getattr(bundle, "version", None)

    predictor = get_predictor()
    resume_result = predictor.predict(payload.resume_text)
    vacancy_result = predictor.predict(payload.vacancy_text)

    matched_skills, missing_skills, extra_resume_skills, skill_score = calculate_skill_match(
        resume_skills=resume_result["skills"],
        vacancy_skills=vacancy_result["skills"],
    )

    category_match = resume_result["category"] == vacancy_result["category"]
    level_match = resume_result["level"] == vacancy_result["level"]

    match_score = calculate_match_score(
        skill_score=skill_score,
        category_match=category_match,
        level_match=level_match,
        resume_confidence=resume_result["confidence"],
        vacancy_confidence=vacancy_result["confidence"],
    )

    explanation = build_match_explanation(
        match_score=match_score,
        category_match=category_match,
        level_match=level_match,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )

    response = _build_match_response(
        resume_result=resume_result,
        vacancy_result=vacancy_result,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        extra_resume_skills=extra_resume_skills,
        category_match=category_match,
        level_match=level_match,
        match_score=match_score,
        explanation=explanation,
        model_version=model_version,
    )

    MatchHistoryRepository(db).create(
        user_id=current_user.id,
        resume_text=payload.resume_text,
        vacancy_text=payload.vacancy_text,
        match_score=response.match_score,
        category_match=response.category_match,
        level_match=response.level_match,
        matched_skills=response.matched_skills,
        missing_skills=response.missing_skills,
        extra_resume_skills=response.extra_resume_skills,
        resume_analysis=response.resume_analysis.model_dump(mode="json"),
        vacancy_analysis=response.vacancy_analysis.model_dump(mode="json"),
        explanation=response.explanation,
        model_version=response.model_version,
    )

    return response

@router.get("/history", response_model=MatchHistoryList)
def list_match_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchHistoryList:
    """Возвращает историю сравнений текущего пользователя."""
    repo = MatchHistoryRepository(db)

    items = repo.list_for_user(
        current_user.id,
        limit=limit,
        offset=offset,
    )
    total = repo.count_for_user(current_user.id)

    return MatchHistoryList(
        items=[MatchHistoryItem.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/history/{match_id}", response_model=MatchHistoryItem)
def get_match_history_item(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchHistoryItem:
    """Возвращает одно сохранённое сравнение по id."""
    item = MatchHistoryRepository(db).get_by_id(
        match_id=match_id,
        user_id=current_user.id,
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сравнение не найдено",
        )

    return MatchHistoryItem.model_validate(item)