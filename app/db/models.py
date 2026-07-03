import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    predictions: Mapped[list["PredictionHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    skills: Mapped[list[str]] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="predictions")
    feedback: Mapped["Feedback | None"] = relationship(
        back_populates="prediction", uselist=False, cascade="all, delete-orphan"
    )


class ModelVersion(Base):
    """Реестр версий ML-моделей (для версионирования и переключения активной модели)."""

    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Feedback(Base):
    """Обратная связь от пользователя для исправления предсказаний модели."""

    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prediction_history.id", ondelete="CASCADE"), unique=True
    )
    correct_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correct_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    prediction: Mapped["PredictionHistory"] = relationship(back_populates="feedback")


class MatchHistory(Base):
    """История сравнений резюме и вакансий."""

    __tablename__ = "match_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_text: Mapped[str] = mapped_column(Text, nullable=False)

    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    category_match: Mapped[bool] = mapped_column(Boolean, nullable=False)
    level_match: Mapped[bool] = mapped_column(Boolean, nullable=False)

    matched_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    extra_resume_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    resume_analysis: Mapped[dict] = mapped_column(JSONB, nullable=False)
    vacancy_analysis: Mapped[dict] = mapped_column(JSONB, nullable=False)

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )