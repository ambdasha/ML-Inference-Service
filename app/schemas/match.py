from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.schemas.prediction import CategoryEnum, LevelEnum
from datetime import datetime
from uuid import UUID

class MatchRequest(BaseModel):
    """Запрос на сравнение резюме и вакансии."""

    resume_text: str = Field(
        min_length=10,
        max_length=settings.MAX_TEXT_LENGTH,
        description="Текст резюме кандидата",
    )
    vacancy_text: str = Field(
        min_length=10,
        max_length=settings.MAX_TEXT_LENGTH,
        description="Текст вакансии",
    )

    @field_validator("resume_text", "vacancy_text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Текст не должен быть пустым")
        return value


class TextAnalysisResult(BaseModel):
    """Краткий результат анализа одного текста."""

    category: CategoryEnum
    level: LevelEnum
    skills: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class MatchResponse(BaseModel):
    """Ответ сервиса сравнения резюме и вакансии."""

    match_score: float = Field(ge=0.0, le=1.0)
    category_match: bool
    level_match: bool

    matched_skills: list[str]
    missing_skills: list[str]
    extra_resume_skills: list[str]

    resume_analysis: TextAnalysisResult
    vacancy_analysis: TextAnalysisResult

    explanation: str
    model_version: str | None = None




class MatchHistoryItem(BaseModel):
    """Один элемент истории сравнений."""

    id: UUID
    resume_text: str
    vacancy_text: str

    match_score: float
    category_match: bool
    level_match: bool

    matched_skills: list[str]
    missing_skills: list[str]
    extra_resume_skills: list[str]

    resume_analysis: TextAnalysisResult
    vacancy_analysis: TextAnalysisResult

    explanation: str
    model_version: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class MatchHistoryList(BaseModel):
    """Список истории сравнений с пагинацией."""

    items: list[MatchHistoryItem]
    total: int
    limit: int
    offset: int