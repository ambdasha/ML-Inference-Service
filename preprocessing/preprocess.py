"""Главный скрипт препроцессинга: сырой resume_data.csv -> dataset.csv
(text, category, level) + отчёт о качестве данных.

"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import PreprocessConfig, setup_logging
from labels import ALL_CATEGORIES, detect_category, detect_level, has_title_override, parse_min_years
from quality_report import DataQualityReport
from text_preprocessor import TextPreprocessor

BOM_COLUMN_FIX = {"\ufeffjob_position_name": "job_position_name"}


def load_raw_dataset(path: str, logger) -> pd.DataFrame:
    logger.info("Читаю сырой датасет: %s", path)
    df = pd.read_csv(path)
    df = df.rename(columns=BOM_COLUMN_FIX)
    logger.info("Загружено %d строк, %d колонок", len(df), df.shape[1])
    return df


def run_pipeline(config: PreprocessConfig, logger) -> tuple[pd.DataFrame, DataQualityReport]:
    report = DataQualityReport()

    df = load_raw_dataset(config.raw_dataset_path, logger)
    report.raw_row_count = len(df)
    report.compute_missing_values(df, config.text_columns + ("job_position_name", "matched_score"))
    report.compute_matched_score_stats(df)

    #дубли по всем колонкам сырого датасета 
    before = len(df)
    df = df.drop_duplicates()
    report.duplicate_rows = before - len(df)
    report.record_drop("точные дубли строк (все колонки)", before - len(df))

    #сборка текста 
    preprocessor = TextPreprocessor(config.text_columns, config.min_text_length)
    df["text"] = preprocessor.transform(df)

    before = len(df)
    df = df[~df["text"].apply(preprocessor.is_too_short)]
    report.record_drop(
        f"текст короче {config.min_text_length} символов после сборки "
        f"({', '.join(config.text_columns)})",
        before - len(df),
    )

    # category из job_position_name 
    before = len(df)
    df["category"] = df["job_position_name"].apply(detect_category)
    n_out_of_scope = df["category"].isna().sum()
    df = df[df["category"].notna()]
    report.record_drop(
        "job_position_name вне таксономии из 4 IT-категорий (не backend/frontend/data_science/analytics)",
        int(n_out_of_scope),
    )
    logger.info("После фильтрации по category осталось %d строк", len(df))

    # фильтр по matched_score
    before = len(df)
    df = df[df["matched_score"] >= config.min_matched_score]
    report.record_drop(
        f"matched_score < {config.min_matched_score} (резюме слабо соответствует вакансии)",
        before - len(df),
    )

    # level из experiencere_requirement + job_position_name 
    df["level"] = df.apply(
        lambda row: detect_level(row["job_position_name"], row.get("experiencere_requirement")),
        axis=1,
    )

 
    is_fallback = df.apply(
        lambda row: has_title_override(row["job_position_name"]) is None
        and parse_min_years(row.get("experiencere_requirement")) is None,
        axis=1,
    )
    fallback_counts = df.loc[is_fallback, "job_position_name"].value_counts().to_dict()
    report.record_level_fallback(fallback_counts)

    result = df[["text", "category", "level"]].copy()
    before = len(result)
    result = result.drop_duplicates()
    report.record_drop("дубли по итоговому тексту (text, category, level)", before - len(result))

    report.final_row_count = len(result)
    report.compute_class_distribution(result)
    report.check_missing_categories(ALL_CATEGORIES)

    return result, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default="config.json", help="Путь к JSON-конфигу")
    parser.add_argument("--raw", type=str, default=None, help="Переопределить raw_dataset_path")
    parser.add_argument("--output", type=str, default=None, help="Переопределить output_dataset_path")
    args = parser.parse_args()

    config = PreprocessConfig.from_json(args.config)
    if args.raw:
        config.raw_dataset_path = args.raw
    if args.output:
        config.output_dataset_path = args.output

    logger = setup_logging(config)
    logger.info("Конфигурация: %s", config.to_dict())

    dataset, report = run_pipeline(config, logger)

    output_path = Path(config.output_dataset_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    logger.info("Датасет сохранён: %s (%d строк)", output_path, len(dataset))

    report.save(config.report_output_path)
    report.log_summary()


if __name__ == "__main__":
    main()
