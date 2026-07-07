from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression

from training.evaluation import evaluate_predictions


DATASET_PATH = Path("training/dataset.csv")
EXPERIMENTS_DIR = Path("models/experiments")
RESULTS_PATH = EXPERIMENTS_DIR / "experiments.csv"
SUMMARY_PATH = EXPERIMENTS_DIR / "best_summary.json"

RANDOM_STATE = 42
TEST_SIZE = 0.2


@dataclass(frozen=True)
class ModelConfig:
    """Описание модели, которую хотим проверить."""

    name: str
    estimator: object


def load_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Загружает датасет и проверяет обязательные колонки."""
    if not path.exists():
        raise FileNotFoundError(
            f"Датасет не найден: {path}. "
            "Сначала запусти python training/generate_dataset.py"
        )

    df = pd.read_csv(path)

    required_columns = {"text", "category", "level"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"В датасете не хватает колонок: {sorted(missing_columns)}")

    df = df.dropna(subset=["text", "category", "level"]).copy()

    df["text"] = df["text"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["level"] = df["level"].astype(str).str.strip()

    df = df[df["text"].str.len() >= 10]

    if df.empty:
        raise ValueError("После очистки датасет оказался пустым")

    return df


def get_model_configs() -> list[ModelConfig]:
    """Возвращает модели, которые сравниваем.

    Здесь специально выбраны простые модели:
    - LogisticRegression — хороший baseline;
    - LinearSVC — часто силён на текстовой классификации;
    - MultinomialNB — очень быстрый baseline для текстов.
    """
    return [
        ModelConfig(
            name="logistic_regression",
            estimator=LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
        ModelConfig(
            name="linear_svc",
            estimator=LinearSVC(
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
        ),
        ModelConfig(
            name="multinomial_nb",
            estimator=MultinomialNB(),
        ),
    ]


def build_pipeline(estimator: object) -> Pipeline:
    """Создаёт pipeline: TF-IDF + модель."""
    return Pipeline(
        steps=[
            (
                "vectorizer",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=20_000,
                ),
            ),
            ("model", estimator),
        ]
    )


def get_model_size_mb(model: Pipeline) -> float:
    """Считает примерный размер модели на диске в мегабайтах."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "model.joblib"
        joblib.dump(model, tmp_path)
        size_bytes = tmp_path.stat().st_size

    return round(size_bytes / (1024 * 1024), 4)


def measure_inference_time_ms(model: Pipeline, texts: list[str]) -> float:
    """Измеряет среднее время инференса на один текст."""
    if not texts:
        return 0.0

    start = time.perf_counter()
    model.predict(texts)
    elapsed = time.perf_counter() - start

    return round((elapsed / len(texts)) * 1000, 4)


# def evaluate_model(
#     *,
#     model: Pipeline,
#     x_test: list[str],
#     y_test: list[str],
# ) -> dict[str, float]:
#     """Считает основные метрики качества."""
#     predictions = model.predict(x_test)

#     return {
#         "accuracy": round(accuracy_score(y_test, predictions), 4),
#         "f1_macro": round(f1_score(y_test, predictions, average="macro"), 4),
#         "f1_weighted": round(f1_score(y_test, predictions, average="weighted"), 4),
#     }


def save_experiment_model(
    *,
    model: Pipeline,
    target: str,
    model_name: str,
) -> Path:
    """Сохраняет обученную экспериментальную модель."""
    model_dir = EXPERIMENTS_DIR / target / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "pipeline.joblib"
    joblib.dump(model, model_path)

    return model_path


def compare_for_target(
    *,
    df: pd.DataFrame,
    target: str,
) -> list[dict]:
    """Сравнивает модели для одной целевой переменной.

    target может быть:
    - category
    - level
    """
    x = df["text"].tolist()
    y = df[target].tolist()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    rows: list[dict] = []

    for config in get_model_configs():
        model = build_pipeline(config.estimator)

        train_start = time.perf_counter()
        model.fit(x_train, y_train)
        train_time_sec = time.perf_counter() - train_start

        predictions = model.predict(x_test)

        metrics = evaluate_predictions(
            y_true=y_test,
            y_pred=predictions,
        )

        inference_time_ms = measure_inference_time_ms(
            model=model,
            texts=x_test,
        )

        model_size_mb = get_model_size_mb(model)

        model_path = save_experiment_model(
            model=model,
            target=target,
            model_name=config.name,
        )

        rows.append(
            {
                "target": target,
                "model_name": config.name,
                "accuracy": metrics.accuracy,
                "f1_macro": metrics.f1_macro,
                "f1_weighted": metrics["f1_weighted"],
                "train_time_sec": round(train_time_sec, 4),
                "inference_time_ms": inference_time_ms,
                "model_size_mb": model_size_mb,
                "model_path": str(model_path),
            }
        )

    return rows


def choose_best_models(results: pd.DataFrame) -> dict:
    """Выбирает лучшую модель для каждого target по macro F1.

    Если macro F1 одинаковый, берём более быструю модель.
    """
    summary: dict[str, dict] = {}

    for target in sorted(results["target"].unique()):
        target_results = results[results["target"] == target].copy()

        target_results = target_results.sort_values(
            by=["f1_macro", "inference_time_ms"],
            ascending=[False, True],
        )

        best = target_results.iloc[0].to_dict()

        summary[target] = {
            "best_model": best["model_name"],
            "f1_macro": best["f1_macro"],
            "accuracy": best["accuracy"],
            "inference_time_ms": best["inference_time_ms"],
            "model_size_mb": best["model_size_mb"],
            "model_path": best["model_path"],
        }

    return summary


def main() -> None:
    """Запускает сравнение моделей и сохраняет результаты."""
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()

    all_rows: list[dict] = []
    all_rows.extend(compare_for_target(df=df, target="category"))
    all_rows.extend(compare_for_target(df=df, target="level"))

    results = pd.DataFrame(all_rows)
    results = results.sort_values(
        by=["target", "f1_macro", "inference_time_ms"],
        ascending=[True, False, True],
    )

    results.to_csv(RESULTS_PATH, index=False)

    summary = choose_best_models(results)

    with SUMMARY_PATH.open("w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(f"Сравнение моделей сохранено: {RESULTS_PATH}")
    print(f"Лучшие модели сохранены: {SUMMARY_PATH}")
    print()
    print(results)


if __name__ == "__main__":
    main()