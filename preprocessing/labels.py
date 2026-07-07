"""Определение category и level вакансии/резюме.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("resume_preprocessing.labels")

# --- Категория -------------------------------------------------------------

ALL_CATEGORIES: set[str] = {"backend", "frontend", "data_science", "analytics"}

JOB_TITLE_CATEGORY: dict[str, str] = {
    "senior software engineer": "backend",
    "database administrator (dba)": "backend",
    "devops engineer": "backend",
    "full stack developer (python,react js)": "backend",
    "ai engineer": "data_science",
    "machine learning (ml) engineer": "data_science",
    "data engineer": "data_science",
    "data science engineer": "data_science",
    "intern (generative ai engineering - 2d/3d image generation)": "data_science",
    "senior ios engineer": "frontend",
}


def normalize_title(title: str | None) -> str:
    if title is None:
        return ""

    return re.sub(r"\s+", " ", str(title)).strip().lower()


def detect_category(job_position_name: str | None) -> str | None:
    """Возвращает category по заголовку вакансии или None, если заголовок
    не относится ни к одной из 4 категорий проекта (см. комментарий выше
    про JOB_TITLE_CATEGORY)."""
    normalized = normalize_title(job_position_name)
    category = JOB_TITLE_CATEGORY.get(normalized)

    if category is None:
        logger.debug("Заголовок вне таксономии, category=None: %r", job_position_name)

    return category

 
TITLE_LEVEL_OVERRIDES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bintern\b", re.IGNORECASE), "intern"),
    (re.compile(r"\btrainee\b", re.IGNORECASE), "intern"),
    (re.compile(r"\bsenior\b", re.IGNORECASE), "senior"),
    (re.compile(r"\blead\b", re.IGNORECASE), "senior"),
    (re.compile(r"\bprincipal\b", re.IGNORECASE), "senior"),
    (re.compile(r"\bhead of\b", re.IGNORECASE), "senior"),
]

# Парсим "At least N year(s)" и "N to M years" -> нижняя граница лет опыта.
_AT_LEAST_RE = re.compile(r"at least\s+(\d+)\s*year", re.IGNORECASE)
_RANGE_RE = re.compile(r"(\d+)\s*to\s*(\d+)\s*years?", re.IGNORECASE)


def parse_min_years(experience_requirement: str | None) -> float | None:
    """Достаёт нижнюю границу требуемого опыта (в годах) из строки вида
    'At least 5 years' или '2 to 5 years'. Возвращает None, если распарсить
    не получилось (чтобы вызывающий код мог явно залогировать это, а не
    молча подставить дефолт)."""
    if not experience_requirement:
        return None

    text = str(experience_requirement)

    match = _AT_LEAST_RE.search(text)
    if match:
        return float(match.group(1))

    match = _RANGE_RE.search(text)
    if match:
        return float(match.group(1))

    return None


def bucket_by_years(years: float) -> str:
    if years < 1:
        return "intern"
    if years <= 2:
        return "junior"
    if years <= 5:
        return "middle"
    return "senior"


def has_title_override(job_position_name: str | None) -> str | None:
    title = job_position_name or ""
    for pattern, level in TITLE_LEVEL_OVERRIDES:
        if pattern.search(title):
            return level
    return None


def detect_level(job_position_name: str | None, experience_requirement: str | None) -> str:
    """Определяет level. Порядок приоритета:
    1. Явное слово в заголовке (Senior/Intern/Lead/...) — самый надёжный сигнал.
    2. Нижняя граница требуемого опыта из experiencere_requirement.
    3. Фолбэк "middle", если ни то, ни другое не сработало.
    """
    override_level = has_title_override(job_position_name)
    if override_level is not None:
        return override_level

    years = parse_min_years(experience_requirement)
    if years is not None:
        return bucket_by_years(years)

    logger.debug(
        "Fallback level='middle' для job_position_name=%r, experience=%r",
        job_position_name, experience_requirement,
    )
    return "middle"
