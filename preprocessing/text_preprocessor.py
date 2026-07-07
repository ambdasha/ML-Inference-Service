"""TextPreprocessor — очистка и сборка текстовых полей резюме в единое поле text.

Вынесен в отдельный класс (а не набор свободных функций), потому что у него
есть состояние (список колонок, min_length), и так его удобно переиспользовать
и тестировать отдельно от остального пайплайна.
"""

from __future__ import annotations

import ast
import logging
import re

import pandas as pd

logger = logging.getLogger("resume_preprocessing.text")

_WHITESPACE_RE = re.compile(r"\s+")


class TextPreprocessor:
    def __init__(self, text_columns: tuple[str, ...], min_text_length: int = 20):
        self.text_columns = text_columns
        self.min_text_length = min_text_length

    @staticmethod
    def _try_parse_list(value: str) -> list[str] | None:
        """Некоторые колонки (positions, related_skils_in_job) хранят
        значения как строковое представление Python-списка, например
        "['Software Developer']" или "['Big Data Analyst', 'Analyst']".
        Пытаемся распарсить их через ast.literal_eval, а не грубой заменой
        символов "[", "]", "'" — так пропадает риск случайно испортить
        текст, где эти символы встречаются не как разделители списка.
        """
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None

        if isinstance(parsed, list):
            return [str(item) for item in parsed if item is not None]

        return None

    def clean_value(self, value) -> str:
        if pd.isna(value):
            return ""

        text = str(value)

        parsed_list = self._try_parse_list(text)
        if parsed_list is not None:
            text = ", ".join(parsed_list)

        text = text.replace("\\n", " ").replace("\n", " ")
        text = _WHITESPACE_RE.sub(" ", text)

        return text.strip()

    def build_text(self, row: pd.Series) -> str:
        parts = []
        for column in self.text_columns:
            if column not in row:
                continue
            cleaned = self.clean_value(row[column])
            if cleaned:
                parts.append(cleaned)

        return " ".join(parts)

    def transform(self, df: pd.DataFrame) -> pd.Series:
        """Применяет build_text ко всему датафрейму, возвращает pd.Series
        с итоговым текстом (пока без фильтрации по min_text_length —
        отбор коротких строк — забота вызывающего кода, у которого есть
        доступ к остальным колонкам для quality report)."""
        return df.apply(self.build_text, axis=1)

    def is_too_short(self, text: str) -> bool:
        return len(text) < self.min_text_length
