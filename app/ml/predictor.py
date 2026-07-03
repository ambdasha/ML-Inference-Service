import numpy as np

from app.ml.model_loader import ModelBundle, get_model_bundle
from app.ml.preprocessing import clean_text, extract_skills


class Predictor:
    """Выполняет предсказание категории, уровня и навыков по тексту вакансии/резюме."""

    def __init__(self, bundle: ModelBundle | None = None) -> None:
        self.bundle = bundle or get_model_bundle()

    def predict(self, text: str) -> dict:
        cleaned = clean_text(text)
        features = self.bundle.vectorizer.transform([cleaned])

        category, category_confidence = self._predict_with_confidence(
            self.bundle.category_model, features
        )
        level, level_confidence = self._predict_with_confidence(self.bundle.level_model, features)

        skills = extract_skills(text)

        # Итоговый confidence — среднее по двум моделям (категория важнее уровня)
        confidence = round(0.6 * category_confidence + 0.4 * level_confidence, 4)

        return {
            "category": category,
            "level": level,
            "skills": skills,
            "confidence": confidence,
        }

    @staticmethod
    def _predict_with_confidence(model, features) -> tuple[str, float]:
        """Возвращает (предсказанный класс, вероятность лучшего класса)."""
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(features)[0]
            best_idx = int(np.argmax(probabilities))
            label = model.classes_[best_idx]
            confidence = float(probabilities[best_idx])
        else:
            # Для моделей без predict_proba (например LinearSVC) используем decision_function
            label = model.predict(features)[0]
            scores = model.decision_function(features)[0]
            scores = np.atleast_1d(scores)
            exp_scores = np.exp(scores - np.max(scores))
            softmax = exp_scores / exp_scores.sum()
            best_idx = int(np.argmax(softmax))
            confidence = float(softmax[best_idx])

        return str(label), round(confidence, 4)


_predictor: Predictor | None = None


def get_predictor() -> Predictor:
    global _predictor
    if _predictor is None:
        _predictor = Predictor()
    return _predictor
