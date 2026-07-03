import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.cache import check_rate_limit
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User
from app.db.repositories import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Извлекает и проверяет JWT, возвращает пользователя из БД."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    user = UserRepository(db).get_by_email(email)
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def enforce_rate_limit(request: Request, user: User = Depends(get_current_user)) -> None:
    """Ограничивает количество запросов на пользователя (см. RATE_LIMIT_* в настройках)."""
    identifier = str(user.id)
    if not check_rate_limit(identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышен лимит запросов. Попробуйте позже.",
        )


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный идентификатор") from exc
