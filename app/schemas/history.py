import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.prediction import CategoryEnum, LevelEnum


class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    input_text: str
    category: CategoryEnum
    level: LevelEnum
    skills: list[str]
    confidence: float
    cached: bool
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: list[HistoryItem]
    limit: int
    offset: int
    total: int
