"""Конфигурация пайплайна препроцессинга резюме.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class PreprocessConfig:
    # --- пути ---
    raw_dataset_path: str = "data/raw/resume_data.csv"
    output_dataset_path: str = "data/processed/dataset.csv"
    report_output_path: str = "data/reports/quality_report.md"

    # --- какие колонки резюме склеиваются в итоговый текст ---
    text_columns: tuple[str, ...] = (
        "career_objective",
        "skills",
        "major_field_of_studies",
        "positions",
        "responsibilities",
    )

    # --- фильтры качества ---

    min_text_length: int = 20
    min_matched_score: float = 0.4

    # --- логирование ---
    log_level: str = "INFO"
    log_file: str | None = None  

    @classmethod
    def from_json(cls, path: str | Path) -> "PreprocessConfig":
        path = Path(path)
        if not path.exists():
            logging.getLogger(__name__).warning(
                "Файл конфигурации %s не найден, используются значения по умолчанию.", path
            )
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            overrides = json.load(f)

        if "text_columns" in overrides:
            overrides["text_columns"] = tuple(overrides["text_columns"])

        return cls(**overrides)

    def to_dict(self) -> dict:
        return asdict(self)


def setup_logging(config: PreprocessConfig) -> logging.Logger:
    logger = logging.getLogger("resume_preprocessing")
    logger.setLevel(config.log_level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if config.log_file:
        Path(config.log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
