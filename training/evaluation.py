from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass(frozen=True)
class EvaluationResult:
    """Результаты оценки модели."""

    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    f1_weighted: float

    report: dict
    confusion_matrix: list[list[int]]

    samples: int


def evaluate_predictions(
    *,
    y_true: list[str],
    y_pred: list[str],
) -> EvaluationResult:
    """
    Вычисляет основные метрики качества классификации.

    Parameters
    ----------
    y_true
        Правильные ответы.

    y_pred
        Предсказания модели.

    Returns
    -------
    EvaluationResult
    """

    report = classification_report(
        y_true,
        y_pred,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
    )

    return EvaluationResult(
        accuracy=round(
            accuracy_score(y_true, y_pred),
            4,
        ),
        precision_macro=round(
            precision_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            4,
        ),
        recall_macro=round(
            recall_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            4,
        ),
        f1_macro=round(
            f1_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0,
            ),
            4,
        ),
        f1_weighted=round(
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0,
            ),
            4,
        ),
        report=report,
        confusion_matrix=matrix.tolist(),
        samples=len(y_true),
    )


def evaluation_to_dataframe(
    result: EvaluationResult,
) -> pd.DataFrame:
    """
    Преобразует результат оценки модели
    в DataFrame.

    Это удобно для сохранения CSV.
    """

    return pd.DataFrame(
        [
            {
                "accuracy": result.accuracy,
                "precision_macro": result.precision_macro,
                "recall_macro": result.recall_macro,
                "f1_macro": result.f1_macro,
                "f1_weighted": result.f1_weighted,
                "samples": result.samples,
            }
        ]
    )


def print_metrics(
    result: EvaluationResult,
) -> None:
    """
    Красиво печатает метрики.
    """

    print()

    print("=" * 50)
    print("Model evaluation")
    print("=" * 50)

    print(f"Samples           : {result.samples}")
    print(f"Accuracy          : {result.accuracy:.4f}")
    print(f"Precision (macro) : {result.precision_macro:.4f}")
    print(f"Recall (macro)    : {result.recall_macro:.4f}")
    print(f"F1 (macro)        : {result.f1_macro:.4f}")
    print(f"F1 (weighted)     : {result.f1_weighted:.4f}")

    print("=" * 50)


def print_classification_report(
    result: EvaluationResult,
) -> None:
    """
    Печатает classification report.
    """

    report_df = (
        pd.DataFrame(result.report)
        .transpose()
        .round(4)
    )

    print()
    print(report_df)


def get_confusion_matrix_dataframe(
    *,
    result: EvaluationResult,
    labels: list[str],
) -> pd.DataFrame:
    """
    Возвращает confusion matrix
    как DataFrame.
    """

    return pd.DataFrame(
        result.confusion_matrix,
        index=labels,
        columns=labels,
    )