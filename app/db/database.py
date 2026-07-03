from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI: предоставляет сессию БД и закрывает её после запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создаёт таблицы в БД на основе моделей (для разработки; в проде — alembic)."""
    from app.db import models  # noqa: F401  (регистрируем модели в Base.metadata)

    Base.metadata.create_all(bind=engine)
