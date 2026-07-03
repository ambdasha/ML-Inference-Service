from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, parse_uuid
from app.db.database import get_db
from app.db.models import User
from app.db.repositories import PredictionRepository
from app.schemas.history import HistoryItem, HistoryListResponse

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryListResponse:
    repo = PredictionRepository(db)
    items = repo.list_for_user(current_user.id, limit=limit, offset=offset)

    return HistoryListResponse(
        items=[HistoryItem.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
        total=len(items),
    )


@router.get("/{history_id}", response_model=HistoryItem)
def get_history_item(
    history_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> HistoryItem:
    item_id = parse_uuid(history_id)
    repo = PredictionRepository(db)
    item = repo.get_by_id(item_id, current_user.id)

    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")

    return HistoryItem.model_validate(item)
