"""Генерирует синтетический датасет вакансий/резюме для обучения моделей.

Датасет синтетический и предназначен для демонстрации пайплайна обучения.
Для реального проекта рекомендуется собрать датасет из открытых источников
(hh.ru API, Kaggle и т.п.) и разметить вручную или с помощью эвристик.
"""

import csv
import itertools
import random

random.seed(42)

OUTPUT_PATH = "training/dataset.csv"

# --- Шаблоны по направлениям -------------------------------------------------

ROLE_PHRASES = {
    "backend": [
        "Ищем backend-разработчика",
        "Требуется backend-инженер",
        "В команду нужен разработчик серверной части",
        "Разработчик backend для развития платформы",
        "Backend developer для высоконагруженного сервиса",
    ],
    "frontend": [
        "Ищем frontend-разработчика",
        "Требуется frontend-инженер",
        "В команду нужен разработчик интерфейсов",
        "Frontend developer для разработки веб-приложения",
        "Разработчик пользовательских интерфейсов",
    ],
    "data_science": [
        "Ищем data scientist",
        "Требуется специалист по машинному обучению",
        "В команду нужен ML-инженер",
        "Data scientist для разработки моделей",
        "Исследователь данных для NLP-проекта",
    ],
    "analytics": [
        "Ищем аналитика данных",
        "Требуется product-аналитик",
        "В команду нужен бизнес-аналитик",
        "Data analyst для анализа метрик продукта",
        "Аналитик для построения дашбордов и отчетов",
    ],
}

SKILLS_PHRASES = {
    "backend": [
        "Python, FastAPI, PostgreSQL, Redis, Docker",
        "Go, PostgreSQL, Redis, Kafka, Docker",
        "Java, Spring Boot, PostgreSQL, Kafka, Docker",
        "Python, Django, PostgreSQL, Celery, RabbitMQ",
        "Python, FastAPI, SQLAlchemy, Alembic, Docker Compose, pytest",
        "Go, gRPC, PostgreSQL, Redis, Kubernetes",
        "PHP, Laravel, MySQL, Redis, Docker",
        "Python, REST API, PostgreSQL, JWT, Swagger",
    ],
    "frontend": [
        "JavaScript, React, Redux, TypeScript, HTML, CSS",
        "TypeScript, React, Next.js, Tailwind CSS",
        "Vue.js, Vuex, JavaScript, HTML, CSS",
        "Angular, TypeScript, RxJS, HTML, CSS",
        "React, GraphQL, TypeScript, Webpack",
        "JavaScript, HTML, CSS, jQuery, Bootstrap",
        "React Native, TypeScript, Redux, REST API",
    ],
    "data_science": [
        "Python, pandas, numpy, scikit-learn, Jupyter",
        "Python, PyTorch, NLP, transformers, Docker",
        "Python, TensorFlow, Computer Vision, OpenCV",
        "Python, scikit-learn, XGBoost, pandas, SQL",
        "Python, машинное обучение, статистика, A/B тесты, pandas",
        "Python, PyTorch, нейронные сети, CUDA, Docker",
        "Python, NLP, BERT, scikit-learn, FastAPI",
    ],
    "analytics": [
        "SQL, Python, Excel, Power BI, A/B тесты",
        "SQL, Tableau, Python, метрики продукта",
        "SQL, Excel, Google Analytics, дашборды",
        "Python, pandas, SQL, Power BI, отчетность",
        "SQL, Looker, Python, продуктовая аналитика",
        "Excel, SQL, статистика, A/B тестирование",
        "SQL, Python, ETL, дашборды, метрики",
    ],
}

RESPONSIBILITIES = {
    "backend": [
        "Разработка и поддержка REST API, работа с базами данных, написание тестов.",
        "Проектирование микросервисов, оптимизация запросов к БД, code review.",
        "Реализация бизнес-логики, интеграция с внешними сервисами, поддержка CI/CD.",
        "Разработка эндпоинтов, работа с очередями сообщений, мониторинг сервиса.",
    ],
    "frontend": [
        "Верстка интерфейсов по макетам, работа с REST API, оптимизация производительности.",
        "Разработка компонентов на React, написание unit-тестов, code review.",
        "Создание адаптивных интерфейсов, интеграция с backend, поддержка дизайн-системы.",
        "Разработка SPA-приложений, работа с состоянием, оптимизация загрузки страниц.",
    ],
    "data_science": [
        "Разработка и обучение ML-моделей, анализ данных, подготовка отчетов о метриках.",
        "Построение пайплайнов обработки данных, исследование гипотез, A/B тестирование.",
        "Обучение и валидация моделей, feature engineering, деплой моделей в production.",
        "Анализ текстовых данных, разработка NLP-моделей, оценка качества классификации.",
    ],
    "analytics": [
        "Построение дашбордов, анализ метрик продукта, подготовка отчетов для менеджмента.",
        "Проведение A/B тестов, анализ воронки конверсии, формулирование гипотез роста.",
        "Сбор и визуализация данных, написание SQL-запросов, автоматизация отчетности.",
        "Анализ пользовательского поведения, расчет unit-экономики, презентация результатов.",
    ],
}

LEVEL_PHRASES = {
    "intern": [
        "Опыт работы не требуется, готовы обучать.",
        "Подойдет стажер без опыта коммерческой разработки.",
        "Ищем студента последних курсов на стажировку.",
        "Без опыта работы, главное — желание учиться.",
        "Стажировка с последующим оформлением в штат.",
    ],
    "junior": [
        "Опыт работы от 6 месяцев до 1 года.",
        "Подойдет junior-специалист с базовыми знаниями.",
        "Опыт коммерческой разработки от 1 года.",
        "Junior-уровень, базовое понимание технологий обязательно.",
        "Небольшой опыт работы, готовность развиваться под руководством senior.",
    ],
    "middle": [
        "Опыт работы от 2 до 4 лет.",
        "Уверенное знание технологий, опыт самостоятельной разработки.",
        "Middle-специалист с опытом проектирования решений.",
        "Опыт работы от 3 лет, умение работать в команде и менторить junior.",
        "Самостоятельная разработка фич от идеи до релиза, опыт от 2 лет.",
    ],
}

CATEGORIES = ["backend", "frontend", "data_science", "analytics"]
LEVELS = ["intern", "junior", "middle"]


def build_text(category: str, level: str, role_idx: int, skill_idx: int, resp_idx: int, level_idx: int) -> str:
    role = ROLE_PHRASES[category][role_idx % len(ROLE_PHRASES[category])]
    skills = SKILLS_PHRASES[category][skill_idx % len(SKILLS_PHRASES[category])]
    responsibilities = RESPONSIBILITIES[category][resp_idx % len(RESPONSIBILITIES[category])]
    level_phrase = LEVEL_PHRASES[level][level_idx % len(LEVEL_PHRASES[level])]

    return f"{role}. Стек: {skills}. {responsibilities} {level_phrase}"


def main() -> None:
    rows: list[tuple[str, str, str]] = []

    for category in CATEGORIES:
        for level in LEVELS:
            # Для каждой комбинации категория/уровень генерируем несколько вариантов текста
            combos = list(itertools.product(range(len(ROLE_PHRASES[category])), range(len(SKILLS_PHRASES[category]))))
            random.shuffle(combos)

            for i, (role_idx, skill_idx) in enumerate(combos[:8]):
                resp_idx = i % len(RESPONSIBILITIES[category])
                level_idx = i % len(LEVEL_PHRASES[level])
                text = build_text(category, level, role_idx, skill_idx, resp_idx, level_idx)
                rows.append((text, category, level))

    random.shuffle(rows)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "category", "level"])
        writer.writerows(rows)

    print(f"Сгенерировано {len(rows)} примеров -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
