"""Обучает TF-IDF векторизатор и две модели логистической регрессии:
  - классификация направления (category): backend / frontend / data_science / analytics
  - классификация уровня (level): intern / junior / middle

Сохраняет артефакты в каталог models/.

Запуск:
    python training/generate_dataset.py   # один раз, для генерации dataset.csv
    python training/train.py
"""

import argparse
import os

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

DATASET_PATH = "training/dataset.csv"
MODELS_DIR = "models"

# Простой список русских стоп-слов, часто встречающихся в описаниях вакансий.
# Слова, несущие сигнал об уровне (опыт, лет, года, от и т.п.), намеренно не убираем.
RUSSIAN_STOPWORDS = [
    "и", "в", "на", "с", "для", "до", "по", "из", "к", "о", "у", "за",
    "не", "что", "это", "как", "а", "но", "или", "то", "так", "же", "ли",
    "знание", "знания", "команду", "команде",
]


def clean_for_training(text: str) -> str:
    return text.lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="Обучение ML-моделей")
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Путь к CSV-файлу датасета для обучения"
    )
    args = parser.parse_args()

    dataset_path = args.data
    if not dataset_path:
        real_data_path = "data/processed/dataset.csv"
        synth_data_path = DATASET_PATH
        if os.path.exists(real_data_path) and os.path.exists(synth_data_path):
            print("Обнаружены оба датасета. Объединяем их для мультиязычного обучения:")
            print(f"  - Реальный (EN): {real_data_path}")
            print(f"  - Синтетический (RU): {synth_data_path}")
            df_real = pd.read_csv(real_data_path)
            df_synth = pd.read_csv(synth_data_path)
            df = pd.concat([df_real, df_synth], ignore_index=True)
            print(f"Итоговый размер объединенного датасета: {len(df)} строк.")
        elif os.path.exists(real_data_path):
            dataset_path = real_data_path
            print(f"Используется реальный предобработанный датасет: {dataset_path}")
            df = pd.read_csv(dataset_path)
        else:
            dataset_path = synth_data_path
            print(f"Используется синтетический датасет по умолчанию: {dataset_path}")
            df = pd.read_csv(dataset_path)
    else:
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(
                f"Не найден файл датасета: {dataset_path}. "
                "Сначала запустите training/generate_dataset.py или preprocessing/preprocess.py"
            )
        df = pd.read_csv(dataset_path)
    df["text_clean"] = df["text"].apply(clean_for_training)

    X_train, X_test, y_cat_train, y_cat_test, y_lvl_train, y_lvl_test = train_test_split(
        df["text_clean"],
        df["category"],
        df["level"],
        test_size=0.2,
        random_state=42,
        stratify=df["category"],
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
        stop_words=RUSSIAN_STOPWORDS,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # --- Модель категории ---
    category_model = LogisticRegression(max_iter=1000, class_weight='balanced')
    category_model.fit(X_train_vec, y_cat_train)

    cat_pred = category_model.predict(X_test_vec)
    print("=== Категория ===")
    print(f"Accuracy: {accuracy_score(y_cat_test, cat_pred):.3f}")
    print(f"F1 (macro): {f1_score(y_cat_test, cat_pred, average='macro'):.3f}")
    print(classification_report(y_cat_test, cat_pred, zero_division=0))

    # --- Модель уровня ---
    level_model = LogisticRegression(max_iter=1000, class_weight='balanced')
    level_model.fit(X_train_vec, y_lvl_train)

    lvl_pred = level_model.predict(X_test_vec)
    print("=== Уровень ===")
    print(f"Accuracy: {accuracy_score(y_lvl_test, lvl_pred):.3f}")
    print(f"F1 (macro): {f1_score(y_lvl_test, lvl_pred, average='macro'):.3f}")
    print(classification_report(y_lvl_test, lvl_pred, zero_division=0))

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(MODELS_DIR, "vectorizer.pkl"))
    joblib.dump(category_model, os.path.join(MODELS_DIR, "category_model.pkl"))
    joblib.dump(level_model, os.path.join(MODELS_DIR, "level_model.pkl"))

    print(f"\nМодели сохранены в {MODELS_DIR}/")


if __name__ == "__main__":
    main()
