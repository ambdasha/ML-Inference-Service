# ML Inference Service

Сервис анализа вакансий и резюме: на вход подаётся текст, на выходе -
определённое направление (`backend` / `frontend` / `data_science` / `analytics`),
ключевые навыки, примерный уровень (`intern` / `junior` / `middle`), confidence модели
и история запросов пользователя.

Стек: **Python, FastAPI, PostgreSQL, Redis, SQLAlchemy + Alembic, scikit-learn,
JWT-аутентификация, pytest, Docker Compose.**

## Возможности

- Регистрация и логин (JWT).
- `/predict` - анализ одного текста (категория, уровень, навыки, confidence).
- `/predict/batch` - пакетный анализ нескольких текстов за один запрос.
- Кэширование одинаковых запросов в Redis (`hash(text + model_version)`).
- Rate limiting (по умолчанию 100 запросов/мин на пользователя) через Redis.
- История предсказаний с пагинацией (`/history`, `/history/{id}`).
- Обратная связь по предсказанию (`/predictions/{id}/feedback`) - для будущего дообучения.
- Реестр версий моделей (`model_versions`) - задел под `/admin/models/{id}/activate`.
- `/health` и `/metrics` (Prometheus: количество предсказаний, латентность,
  cache hit rate, средний confidence, ошибки).

## Структура проекта

```
ml-inference-service/
├── app/
│   ├── main.py              # точка входа FastAPI
│   ├── api/                 # роутеры: auth, predict, history
│   ├── core/                # config, security (JWT), cache (Redis), metrics, logging
│   ├── db/                  # database, models (SQLAlchemy), repositories
│   ├── ml/                  # preprocessing, model_loader, predictor
│   └── schemas/              # Pydantic-схемы
├── training/
│   ├── generate_dataset.py  # генерация синтетического датасета
│   ├── dataset.csv
│   └── train.py              # обучение TF-IDF + LogisticRegression
├── models/                   # сохранённые артефакты (vectorizer.pkl, *_model.pkl)
├── migrations/               # Alembic
├── tests/                     # pytest
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Быстрый старт (Docker)

```bash
cp .env.example .env

# 1. Сгенерировать датасет и обучить модели (один раз, локально)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python training/generate_dataset.py
python training/train.py

# 2. Поднять сервисы
docker compose up --build
```

После запуска:
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Метрики: http://localhost:8000/metrics

Применить миграции (после старта `db`):

```bash
docker compose exec api alembic upgrade head
```

> Для разработки таблицы также создаются автоматически при старте приложения
> через `init_db()` (см. `app/db/database.py`), но в проде используйте Alembic.

## Пример запроса

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=user@example.com&password=strongpassword123" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)

curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Ищем backend-разработчика на Go. PostgreSQL, Redis, Kafka, Docker..."}'
```

Пример ответа:

```json
{
  "category": "backend",
  "level": "junior",
  "skills": ["Go", "PostgreSQL", "Redis", "Kafka", "Docker"],
  "confidence": 0.87,
  "cached": false
}
```

## Обучение модели

Модель - TF-IDF (униграммы + биграммы) + две независимые логистические
регрессии: одна предсказывает `category`, другая - `level`. Навыки
извлекаются отдельно по словарю технологий (`app/ml/preprocessing.py`),
не моделью.

```bash
python training/generate_dataset.py   # пересоздать training/dataset.csv
python training/train.py              # обучить и сохранить models/*.pkl
```

## Тесты

```bash
pytest
```

Тестам нужны PostgreSQL (для `tests/conftest.py`, переменная `DATABASE_URL`,
по умолчанию `ml_inference_test`) - Redis в тестах подменяется на `fakeredis`,
а ML-модель - на детерминированный мок.

## Архитектура

```
Client → FastAPI (Auth middleware, JWT) → Prediction Service
                                              ├─ Redis: кэш предсказаний, rate limit
                                              ├─ ML Model: TF-IDF + LogisticRegression
                                              └─ PostgreSQL: users, prediction_history,
                                                              model_versions, feedback
```
