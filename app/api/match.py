from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_current_user
from app.db.database import get_db
from app.db.models import User
from app.ml.matcher import (
    build_match_explanation,
    calculate_match_score,
    calculate_skill_match,
)
from app.ml.model_loader import get_model_bundle
from app.ml.predictor import Predictor
from app.schemas.match import MatchRequest, MatchResponse, TextAnalysisResult

router = APIRouter(prefix="/match", tags=["match"])

predictor = Predictor()


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
    """Сравнивает резюме кандидата с текстом вакансии."""
    bundle = get_model_bundle(db)

    resume_result = predictor.predict(payload.resume_text, bundle)
    vacancy_result = predictor.predict(payload.vacancy_text, bundle)

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

    return MatchResponse(
        match_score=match_score,
        category_match=category_match,
        level_match=level_match,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        extra_resume_skills=extra_resume_skills,
        resume_analysis=TextAnalysisResult(**resume_result),
        vacancy_analysis=TextAnalysisResult(**vacancy_result),
        explanation=explanation,
        model_version=bundle.version,
    )