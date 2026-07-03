import re

# Словарь известных навыков/технологий для извлечения из текста.
# Ключ — то, как навык будет показан в ответе, значение — варианты написания для поиска.
SKILLS_DICTIONARY: dict[str, list[str]] = {
    "Python": ["python"],
    "Go": ["go", "golang"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "SQL": ["sql"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "React": ["react", "react.js", "reactjs"],
    "Vue": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular"],
    "Node.js": ["node.js", "node js", "nodejs", "node"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Kafka": ["kafka"],
    "RabbitMQ": ["rabbitmq"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git"],
    "CI/CD": ["ci/cd", "ci\\cd", "cicd"],
    "Linux": ["linux"],
    "AWS": ["aws"],
    "GCP": ["gcp"],
    "Azure": ["azure"],
    "pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow"],
    "Machine Learning": ["machine learning", "ml", "машинное обучение"],
    "Pydantic": ["pydantic"],
    "SQLAlchemy": ["sqlalchemy"],
    "Celery": ["celery"],
    "GraphQL": ["graphql"],
    "REST API": ["rest api", "restful", "rest"],
    "HTML": ["html"],
    "CSS": ["css"],
    "Excel": ["excel"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],
    "ETL": ["etl"],
    "Airflow": ["airflow"],
    "Spark": ["spark"],
    "Hadoop": ["hadoop"],
}


def clean_text(text: str) -> str:
    """Нормализует текст: нижний регистр, удаление лишних символов и пробелов."""
    text = text.lower()
    text = re.sub(r"[^\w\s\+\#\./\\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_skills(text: str) -> list[str]:
    """Находит в тексте упоминания известных навыков/технологий из словаря.

    Возвращает список уникальных навыков в порядке их обнаружения.
    """
    normalized = text.lower()
    found: list[str] = []

    for skill_name, variants in SKILLS_DICTIONARY.items():
        for variant in variants:
            pattern = r"(?<!\w)" + re.escape(variant) + r"(?!\w)"
            if re.search(pattern, normalized):
                found.append(skill_name)
                break

    return found
