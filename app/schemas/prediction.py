from enum import Enum

from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    backend = "backend"
    frontend = "frontend"
    data_science = "data_science"
    analytics = "analytics"


class LevelEnum(str, Enum):
    intern = "intern"
    junior = "junior"
    middle = "middle"


class PredictRequest(BaseModel):
    text: str = Field(min_length=10, max_length=10_000, description="Текст вакансии или резюме")


class PredictResponse(BaseModel):
    category: CategoryEnum
    level: LevelEnum
    skills: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    cached: bool


class FeedbackRequest(BaseModel):
    correct_category: CategoryEnum | None = None
    correct_level: LevelEnum | None = None
    comment: str | None = Field(default=None, max_length=1000)
