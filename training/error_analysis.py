from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

from training.evaluation import (
    evaluate_predictions,
    evaluation_to_dataframe,
)

DATASET_PATH = Path("training/dataset.csv")

ERROR_DIR = Path("models/error_analysis")

CATEGORY_MODEL = Path("models/category_model.pkl")
CATEGORY_VECTORIZER = Path("models/vectorizer.pkl")

RANDOM_STATE = 42
TEST_SIZE = 0.2

def load_dataset(path: Path | None = None) -> pd.DataFrame:
    """
    Загружает датасет.
    """
    if path is None:
        real_data_path = Path("data/processed/dataset.csv")
        synth_data_path = DATASET_PATH
        if real_data_path.exists() and synth_data_path.exists():
            print("Обнаружены оба датасета. Объединяем их для мультиязычного анализа ошибок:")
            print(f"  - Реальный (EN): {real_data_path}")
            print(f"  - Синтетический (RU): {synth_data_path}")
            df_real = pd.read_csv(real_data_path)
            df_synth = pd.read_csv(synth_data_path)
            df = pd.concat([df_real, df_synth], ignore_index=True)
            print(f"Итоговый размер объединенного датасета: {len(df)} строк.")
            return df
        elif real_data_path.exists():
            path = real_data_path
            print(f"Используется реальный предобработанный датасет: {path}")
        else:
            path = synth_data_path
            print(f"Используется синтетический датасет по умолчанию: {path}")

    if not path.exists():
        raise FileNotFoundError(
            f"Датасет не найден: {path}. "
            "Сначала запустите training/generate_dataset.py или preprocessing/preprocess.py"
        )

    df = pd.read_csv(path)

    df = df.dropna()

    df["text"] = (
        df["text"]
        .astype(str)
        .str.strip()
    )

    return df

def load_pipeline():

    model = joblib.load(CATEGORY_MODEL)
    vectorizer = joblib.load(CATEGORY_VECTORIZER)

    return model, vectorizer

def split_dataset(df: pd.DataFrame):

    return train_test_split(
        df["text"],
        df["category"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df["category"],
    )

def predict(
    model,
    vectorizer,
    x_test,
):

    vectors = vectorizer.transform(x_test)

    predictions = model.predict(vectors)

    return predictions

def build_errors_dataframe(
    *,
    texts,
    y_true,
    y_pred,
):

    rows = []

    for text, real, pred in zip(
        texts,
        y_true,
        y_pred,
    ):

        rows.append(
            {
                "text": text,
                "true_label": real,
                "predicted_label": pred,
                "correct": real == pred,
            }
        )

    return pd.DataFrame(rows)

def save_hard_examples(
    errors: pd.DataFrame,
):

    hard = errors[
        errors["correct"] == False
    ]

    hard.to_csv(
        ERROR_DIR / "hard_examples.csv",
        index=False,
    )

def save_false_positive(
    errors: pd.DataFrame,
    target_class: str = "backend",
):
    # Ложноположительные: предсказали target_class, но на самом деле там другой класс
    fp = errors[
        (errors["correct"] == False) & (errors["predicted_label"] == target_class)
    ]

    fp.to_csv(
        ERROR_DIR / "false_positive_examples.csv",
        index=False,
    )

def save_false_negative(
    errors: pd.DataFrame,
    target_class: str = "backend",
):
    # Ложноотрицательные: на самом деле target_class, но предсказали другой класс
    fn = errors[
        (errors["correct"] == False) & (errors["true_label"] == target_class)
    ]

    fn.to_csv(
        ERROR_DIR / "false_negative_examples.csv",
        index=False,
    )

def main():
    parser = argparse.ArgumentParser(description="Анализ ошибок ML-модели")
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Путь к CSV-файлу датасета для анализа"
    )
    args = parser.parse_args()

    ERROR_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data_path = Path(args.data) if args.data else None
    df = load_dataset(data_path)

    x_train, x_test, y_train, y_test = split_dataset(df)

    model, vectorizer = load_pipeline()

    predictions = predict(
        model,
        vectorizer,
        x_test,
    )

    evaluation = evaluate_predictions(
        y_true=list(y_test),
        y_pred=list(predictions),
    )

    evaluation_to_dataframe(
        evaluation,
    ).to_csv(
        ERROR_DIR / "metrics.csv",
        index=False,
    )

    with open(
        ERROR_DIR / "classification_report.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            evaluation.report,
            file,
            indent=4,
            ensure_ascii=False,
        )

    confusion = pd.DataFrame(
        evaluation.confusion_matrix,
    )

    confusion.to_csv(
        ERROR_DIR / "confusion_matrix.csv",
        index=False,
    )

    errors = build_errors_dataframe(
        texts=x_test,
        y_true=y_test,
        y_pred=predictions,
    )

    save_hard_examples(errors)

    save_false_positive(errors)

    save_false_negative(errors)

    print()

    print("Error analysis completed.")

    print(ERROR_DIR)

if __name__ == "__main__":
    main()


