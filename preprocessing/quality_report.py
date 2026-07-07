"""DataQualityReport — считает и сохраняет отчёт о качестве данных на всех
этапах пайплайна: пропуски, дубли, воронка отброшенных строк по причинам,
распределение классов.

Идея с "воронкой" (funnel): вместо одного финального числа "осталось N строк"
отчёт показывает, СКОЛЬКО строк отвалилось на каждом конкретном шаге и почему
(дубли, пустой текст, вне таксономии категорий, низкий matched_score). Это
как раз то, что обычно спрашивают на защите/собеседовании про ML-пайплайн:
"а как вы фильтровали данные и почему именно так".
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger("resume_preprocessing.quality")


@dataclass
class DataQualityReport:
    raw_row_count: int = 0
    missing_values: dict[str, int] = field(default_factory=dict)
    duplicate_rows: int = 0
    drop_funnel: list[tuple[str, int]] = field(default_factory=list)
    final_row_count: int = 0
    category_distribution: dict[str, int] = field(default_factory=dict)
    level_distribution: dict[str, int] = field(default_factory=dict)
    matched_score_stats: dict[str, float] = field(default_factory=dict)
    level_fallback_by_title: dict[str, int] = field(default_factory=dict)
    missing_categories: list[str] = field(default_factory=list)

    def record_drop(self, reason: str, n_dropped: int) -> None:
        if n_dropped <= 0:
            return
        self.drop_funnel.append((reason, n_dropped))
        logger.info("Отброшено %d строк: %s", n_dropped, reason)

    def compute_missing_values(self, df: pd.DataFrame, columns: tuple[str, ...]) -> None:
        self.missing_values = {
            col: int(df[col].isna().sum()) for col in columns if col in df.columns
        }

    def compute_matched_score_stats(self, df: pd.DataFrame, column: str = "matched_score") -> None:
        if column not in df.columns:
            return
        described = df[column].describe()
        self.matched_score_stats = {
            "mean": round(float(described["mean"]), 4),
            "std": round(float(described["std"]), 4),
            "min": round(float(described["min"]), 4),
            "max": round(float(described["max"]), 4),
        }

    def compute_class_distribution(self, df: pd.DataFrame) -> None:
        if "category" in df.columns:
            self.category_distribution = df["category"].value_counts().to_dict()
        if "level" in df.columns:
            self.level_distribution = df["level"].value_counts().to_dict()

    def check_missing_categories(self, all_categories: set[str]) -> None:
        present = set(self.category_distribution.keys())
        self.missing_categories = sorted(all_categories - present)
        for category in self.missing_categories:
            logger.warning(
                "В итоговом датасете НЕТ ни одной строки категории '%s' — "
                "в исходных данных не нашлось подходящих заголовков вакансий.",
                category,
            )

    def record_level_fallback(self, fallback_counts_by_title: dict[str, int]) -> None:
        self.level_fallback_by_title = fallback_counts_by_title
        total = sum(fallback_counts_by_title.values())
        if total:
            logger.warning(
                "Level='middle' по fallback (нет experiencere_requirement и нет "
                "слова-подсказки в заголовке) для %d строк: %s",
                total, fallback_counts_by_title,
            )

    def to_markdown(self) -> str:
        lines = ["# Отчёт о качестве данных", ""]

        lines.append(f"- Строк в исходном датасете: **{self.raw_row_count}**")
        lines.append(f"- Дублей (по всем колонкам): **{self.duplicate_rows}**")
        lines.append(f"- Строк в итоговом датасете: **{self.final_row_count}**")
        retention = (self.final_row_count / self.raw_row_count * 100) if self.raw_row_count else 0
        lines.append(f"- Доля сохранённых строк: **{retention:.1f}%**")
        lines.append("")

        lines.append("## Пропуски по ключевым колонкам")
        for col, count in self.missing_values.items():
            pct = (count / self.raw_row_count * 100) if self.raw_row_count else 0
            lines.append(f"- `{col}`: {count} ({pct:.1f}%)")
        lines.append("")

        lines.append("## Воронка отброшенных строк")
        for reason, n in self.drop_funnel:
            lines.append(f"- {reason}: -{n}")
        lines.append("")

        if self.matched_score_stats:
            lines.append("## matched_score (исходный датасет)")
            for stat, value in self.matched_score_stats.items():
                lines.append(f"- {stat}: {value}")
            lines.append("")

        lines.append("## Распределение по category (итоговый датасет)")
        for category, count in sorted(self.category_distribution.items()):
            lines.append(f"- {category}: {count}")
        if self.missing_categories:
            lines.append("")
            lines.append(
                f"⚠️ **Категории без единой строки в итоговом датасете:** "
                f"{', '.join(self.missing_categories)} — в исходных данных не "
                f"нашлось подходящих заголовков вакансий для этих категорий."
            )
        lines.append("")

        lines.append("## Распределение по level (итоговый датасет)")
        for level, count in sorted(self.level_distribution.items()):
            lines.append(f"- {level}: {count}")
        lines.append("")

        if self.level_fallback_by_title:
            lines.append("## Level определён по fallback ('middle'), т.к. нет experiencere_requirement и слова-подсказки в заголовке")
            for title, count in sorted(self.level_fallback_by_title.items(), key=lambda kv: -kv[1]):
                lines.append(f"- {title}: {count} строк")
            lines.append("")

        return "\n".join(lines)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_markdown(), encoding="utf-8")
        logger.info("Отчёт о качестве данных сохранён в %s", path)

    def log_summary(self) -> None:
        logger.info(
            "Итог: %d -> %d строк (%.1f%% сохранено), категорий: %d, уровней: %d",
            self.raw_row_count,
            self.final_row_count,
            (self.final_row_count / self.raw_row_count * 100) if self.raw_row_count else 0,
            len(self.category_distribution),
            len(self.level_distribution),
        )
