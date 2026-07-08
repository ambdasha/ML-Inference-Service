import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Feedback, MatchHistory, PredictionHistory, User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class PredictionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        input_text: str,
        category: str,
        level: str,
        skills: list[str],
        confidence: float,
        cached: bool,
        model_version: str | None = None,
    ) -> PredictionHistory:
        record = PredictionHistory(
            user_id=user_id,
            input_text=input_text,
            category=category,
            level=level,
            skills=skills,
            confidence=confidence,
            cached=cached,
            model_version=model_version,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, prediction_id: uuid.UUID, user_id: uuid.UUID) -> PredictionHistory | None:
        return self.db.scalar(
            select(PredictionHistory).where(
                PredictionHistory.id == prediction_id,
                PredictionHistory.user_id == user_id,
            )
        )

    def list_for_user(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> list[PredictionHistory]:
        stmt = (
            select(PredictionHistory)
            .where(PredictionHistory.user_id == user_id)
            .order_by(PredictionHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(stmt))

    def count_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(PredictionHistory.id)).where(PredictionHistory.user_id == user_id)
        return int(self.db.scalar(stmt) or 0)


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(
        self,
        prediction_id: uuid.UUID,
        correct_category: str | None,
        correct_level: str | None,
        comment: str | None,
    ) -> Feedback:
        existing = self.db.scalar(select(Feedback).where(Feedback.prediction_id == prediction_id))
        if existing:
            existing.correct_category = correct_category
            existing.correct_level = correct_level
            existing.comment = comment
        else:
            existing = Feedback(
                prediction_id=prediction_id,
                correct_category=correct_category,
                correct_level=correct_level,
                comment=comment,
            )
            self.db.add(existing)

        self.db.commit()
        self.db.refresh(existing)
        return existing

class MatchHistoryRepository:
    """Работа с историей сравнений резюме и вакансий."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: uuid.UUID,
        resume_text: str,
        vacancy_text: str,
        match_score: float,
        category_match: bool,
        level_match: bool,
        matched_skills: list[str],
        missing_skills: list[str],
        extra_resume_skills: list[str],
        resume_analysis: dict,
        vacancy_analysis: dict,
        explanation: str,
        model_version: str | None,
    ) -> MatchHistory:
        record = MatchHistory(
            user_id=user_id,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            match_score=match_score,
            category_match=category_match,
            level_match=level_match,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            extra_resume_skills=extra_resume_skills,
            resume_analysis=resume_analysis,
            vacancy_analysis=vacancy_analysis,
            explanation=explanation,
            model_version=model_version,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return record

    def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MatchHistory]:
        stmt = (
            select(MatchHistory)
            .where(MatchHistory.user_id == user_id)
            .order_by(MatchHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(stmt).all())

    def count_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(MatchHistory.id)).where(MatchHistory.user_id == user_id)
        return int(self.db.scalar(stmt) or 0)

    def get_by_id(
        self,
        *,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> MatchHistory | None:
        stmt = select(MatchHistory).where(
            MatchHistory.id == match_id,
            MatchHistory.user_id == user_id,
        )

        return self.db.scalar(stmt)
