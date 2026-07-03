from __future__ import annotations


def normalize_skills(skills: list[str]) -> set[str]:
    """Приводит навыки к единому виду для сравнения."""
    return {skill.strip().lower() for skill in skills if skill.strip()}


def calculate_skill_match(
    resume_skills: list[str],
    vacancy_skills: list[str],
) -> tuple[list[str], list[str], list[str], float]:
    """Сравнивает навыки из резюме и вакансии.

    Возвращает:
    - matched_skills: навыки, которые есть и в резюме, и в вакансии;
    - missing_skills: навыки, которые требуются в вакансии, но отсутствуют в резюме;
    - extra_resume_skills: навыки, которые есть в резюме, но не требуются в вакансии;
    - skill_score: доля совпавших навыков от требуемых.
    """
    
    resume_set = normalize_skills(resume_skills)
    vacancy_set = normalize_skills(vacancy_skills)

    if not vacancy_set:
        return [], [], sorted(resume_set), 0.0

    matched = resume_set & vacancy_set
    missing = vacancy_set - resume_set
    extra = resume_set - vacancy_set

    skill_score = len(matched) / len(vacancy_set)

    return (
        sorted(matched),
        sorted(missing),
        sorted(extra),
        round(skill_score, 4),
    )


def calculate_match_score(
    *,
    skill_score: float,
    category_match: bool,
    level_match: bool,
    resume_confidence: float,
    vacancy_confidence: float,
) -> float:
    """Считает общий match_score.

    Логика:
    - навыки важнее всего;
    - совпадение направления тоже очень важно;
    - совпадение уровня полезно, но не главное;
    - confidence снижает итоговую оценку, если модель не уверена.
    """
    category_score = 1.0 if category_match else 0.0
    level_score = 1.0 if level_match else 0.0

    base_score = (
        0.6 * skill_score
        + 0.3 * category_score
        + 0.1 * level_score
    )

    confidence_penalty = (resume_confidence + vacancy_confidence) / 2

    final_score = base_score * confidence_penalty

    return round(final_score, 4)


def build_match_explanation(
    *,
    match_score: float,
    category_match: bool,
    level_match: bool,
    matched_skills: list[str],
    missing_skills: list[str],
) -> str:
    """Создаёт короткое текстовое объяснение результата."""
    parts: list[str] = []

    if match_score >= 0.75:
        parts.append("Резюме хорошо подходит под вакансию.")
    elif match_score >= 0.45:
        parts.append("Резюме частично подходит под вакансию.")
    else:
        parts.append("Резюме слабо подходит под вакансию.")

    if category_match:
        parts.append("Направление резюме совпадает с направлением вакансии.")
    else:
        parts.append("Направление резюме отличается от направления вакансии.")

    if level_match:
        parts.append("Уровень кандидата совпадает с уровнем вакансии.")
    else:
        parts.append("Уровень кандидата отличается от уровня вакансии.")

    if matched_skills:
        parts.append(f"Совпавшие навыки: {', '.join(matched_skills)}.")

    if missing_skills:
        parts.append(f"Не хватает навыков: {', '.join(missing_skills)}.")

    return " ".join(parts)