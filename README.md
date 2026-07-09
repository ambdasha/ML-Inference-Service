# ML Inference Service

**ML Inference Service** — backend-сервис на FastAPI для анализа текстов вакансий и резюме.

Сервис умеет:

- определять IT-направление текста: `backend`, `frontend`, `data_science`, `analytics`;
- определять примерный уровень: `intern`, `junior`, `middle`, `senior` (на русском и английском языках);
- извлекать навыки и технологии из текста;
- сравнивать резюме с вакансией и считать `match_score`;
- сохранять историю предсказаний и сравнений для каждого пользователя;
- принимать обратную связь по предсказаниям для будущего дообучения модели;
- отдавать метрики для Prometheus и Grafana.

---

## Стек

- **Python 3.12**
- **FastAPI** — REST API и Swagger UI
- **PostgreSQL** — хранение пользователей, истории, feedback и match history
- **Redis** — кэширование предсказаний и rate limiting
- **SQLAlchemy 2.0** — ORM
- **Alembic** — миграции БД
- **scikit-learn** — ML-модели
- **TF-IDF + LogisticRegression** — классификация текста
- **JWT** — авторизация пользователей
- **Prometheus** — сбор метрик
- **Grafana** — визуализация метрик
- **pytest** — тесты
- **Docker Compose** — запуск всей инфраструктуры

---


## Что делает сервис

### 1. Анализ одного текста

Эндпоинт `/predict` принимает текст вакансии или резюме и возвращает:

- категорию текста;
- уровень кандидата/вакансии;
- список найденных навыков;
- confidence модели;
- информацию, пришёл ли ответ из кэша.

---

### 2. Пакетный анализ текстов

Эндпоинт `/predict/batch` принимает список текстов и возвращает список предсказаний.
Удобно, если нужно обработать сразу несколько вакансий или несколько резюме.

---

### 3. Сравнение резюме и вакансии

Эндпоинт `/match` принимает:

- `resume_text` — текст резюме;
- `vacancy_text` — текст вакансии.

Сервис отдельно анализирует оба текста, сравнивает навыки, направление и уровень, после чего считает итоговый `match_score` от `0.0` до `1.0`.

Пример результата:

```json
{
  "match_score": 0.81,
  "category_match": true,
  "level_match": true,
  "matched_skills": ["python", "postgresql", "redis", "docker"],
  "missing_skills": ["kafka"],
  "extra_resume_skills": ["fastapi"],
  "resume_analysis": {
    "category": "backend",
    "level": "junior",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
    "confidence": 0.9
  },
  "vacancy_analysis": {
    "category": "backend",
    "level": "junior",
    "skills": ["Python", "PostgreSQL", "Redis", "Kafka", "Docker"],
    "confidence": 0.88
  },
  "explanation": "Резюме хорошо подходит под вакансию. Направление резюме совпадает с направлением вакансии. Уровень кандидата совпадает с уровнем вакансии. Совпавшие навыки: docker, postgresql, python, redis. Не хватает навыков: kafka.",
  "model_version": "v1"
}
```

---

## Как считается `match_score`

Итоговая оценка строится не только по навыкам.

Внутри используется логика:

```text
base_score = 0.6 * skill_score + 0.3 * category_score + 0.1 * level_score
final_score = base_score * average_confidence
```

Где:
- `skill_score` — доля навыков вакансии, которые есть в резюме;
- `category_score` — `1.0`, если направление совпало, иначе `0.0`;
- `level_score` — `1.0`, если уровень совпал, иначе `0.0`;
- `average_confidence` — средняя уверенность модели по резюме и вакансии.

Навыки имеют самый большой вес, потому что для практической оценки соответствия резюме вакансии они важнее всего.

---


## Структура проекта

```text
ml-inference-service/
├── app/
│   ├── main.py                 # точка входа FastAPI
│   ├── api/                    # роутеры API
│   │   ├── auth.py             # регистрация и логин
│   │   ├── predict.py          # предсказания и feedback
│   │   ├── match.py            # сравнение резюме и вакансии
│   │   └── history.py          # история предсказаний
│   ├── core/                   # настройки, JWT, Redis, метрики, логирование
│   ├── db/                     # SQLAlchemy-модели, сессии, репозитории
│   ├── ml/                     # загрузка моделей, предиктор, matcher, preprocessing
│   └── schemas/                # Pydantic-схемы запросов и ответов
│
├── data/                       # данные и отчеты
│   ├── raw/                    # сырые данные (resume_data.csv)
│   ├── processed/              # очищенный реальный датасет (dataset.csv)
│   └── reports/                # отчеты о качестве данных (quality_report.md)
│
├── migrations/                 # Alembic-миграции
│   └── versions/
│       ├── 0001_initial.py
│       └── 0002_match_history.py
│
├── models/                     # обученные ML-артефакты
│   ├── vectorizer.pkl
│   ├── category_model.pkl
│   ├── level_model.pkl
│   ├── experiments/            # результаты сравнения моделей
│   └── error_analysis/         # результаты анализа ошибок
│
├── preprocessing/              # предобработка реальных резюме
│   ├── config.json             # настройки предобработки
│   ├── config.py
│   ├── labels.py               # словари соответствий
│   ├── preprocess.py           # запуск пайплайна
│   ├── quality_report.py       # расчет метрик качества
│   └── text_preprocessor.py    # очистка текстов
│
├── training/                   # генерация датасета и обучение моделей
│   ├── dataset.csv             # синтетический датасет
│   ├── generate_dataset.py     # синтетический генератор (RU)
│   ├── train.py                # скрипт обучения моделей (RU + EN)
│   ├── compare_models.py       # скрипт сравнения алгоритмов
│   └── error_analysis.py       # скрипт выгрузки FP/FN примеров
│
├── monitoring/
│   └── prometheus.yml          # настройка сбора метрик Prometheus
│
├── tests/                      # pytest-тесты
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## API

### Auth

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/auth/register` | регистрация пользователя |
| `POST` | `/auth/login` | логин и получение JWT-токена |

### Prediction

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/predict` | анализ одного текста |
| `POST` | `/predict/batch` | анализ списка текстов |
| `POST` | `/predictions/{prediction_id}/feedback` | отправка исправления по предсказанию |

### History

| Метод | URL | Назначение |
|---|---|---|
| `GET` | `/history` | история предсказаний текущего пользователя |
| `GET` | `/history/{history_id}` | одна запись из истории предсказаний |

### Match

| Метод | URL | Назначение |
|---|---|---|
| `POST` | `/match` | сравнение резюме и вакансии |
| `GET` | `/match/history` | история сравнений текущего пользователя |
| `GET` | `/match/history/{match_id}` | одно сохранённое сравнение |

### System

| Метод | URL | Назначение |
|---|---|---|
| `GET` | `/health` | проверка, что API живой |
| `GET` | `/metrics` | метрики Prometheus |

---

## Быстрый запуск через Docker Compose

В текущей версии проекта модели уже лежат в папке `models/`, поэтому сервис можно запускать сразу.

```bash
cp .env.example .env
docker compose up --build
```

При запуске контейнер `api` автоматически выполняет миграции.

**Порты баз данных**:
Для предотвращения конфликтов с локально запущенными службами PostgreSQL на хост-компьютере, порт базы данных проброшен наружу на порт **`5435`** (вместо стандартного `5432`). Все внутренние связи контейнеров Docker продолжают безопасно работать на порту `5432`.

После запуска будут доступны:

- Веб-интерфейс (SPA): `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Метрики API: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

Данные для входа в Grafana по умолчанию:

```text
login: admin
password: admin
```

---

## Переменные окружения

Основные настройки лежат в `.env.example`.

---

## Примеры запросов

### Регистрация

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "strongpassword123"
  }'
```

---

### Сравнение резюме и вакансии

```bash
curl -X POST http://localhost:8000/match \
  -H "Authorization: Bearer jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Backend-разработчик. Python, FastAPI, PostgreSQL, Redis, Docker. Делала REST API и работала с SQLAlchemy.",
    "vacancy_text": "Ищем junior backend-разработчика. Требования: Python, PostgreSQL, Redis, Kafka, Docker, REST API."
  }'
```

---


## ML-часть

В проекте используется простая и объяснимая ML-схема:

```text
text -> preprocessing -> TF-IDF -> LogisticRegression -> category / level
```

Сохраняются три артефакта:

| Файл | Назначение |
|---|---|
| `models/vectorizer.pkl` | TF-IDF-векторизатор |
| `models/category_model.pkl` | модель классификации направления |
| `models/level_model.pkl` | модель классификации уровня |

Категория и уровень предсказываются ML-моделями, а навыки извлекаются отдельно через словарь технологий из `app/ml/preprocessing.py`.

---

## Предобработка реальных данных и обучение моделей

### 1. Предобработка реального датасета резюме
Для очистки и подготовки реальных данных из сырого CSV-файла запустите скрипт предобработки:
```bash
python preprocessing/preprocess.py
```
Скрипт считывает сырые данные из `data/raw/resume_data.csv`, чистит их, фильтрует по качеству и сохраняет обработанный датасет в `data/processed/dataset.csv`, а также генерирует детальный отчет о качестве в `data/reports/quality_report.md`.

### 2. Генерация синтетических данных
Для генерации синтетических данных на русском языке:
```bash
python training/generate_dataset.py
```
Скрипт создаст файл `training/dataset.csv` (128 строк), содержащий сгенерированные тексты для всех направлений и уровней (включая `senior`).

### 3. Обучение моделей (Мультиязычный режим)
Запуск скрипта обучения:
```bash
python training/train.py
```
**Особенности обучения**:
- Скрипт автоматически проверяет наличие реального датасета (`data/processed/dataset.csv`) и синтетического датасета (`training/dataset.csv`).
- Если обнаружены оба файла, они **автоматически объединяются** для обучения мультиязычной модели. Модель сможет классифицировать резюме и вакансии как на русском, так и на английском языках.
- Вы также можете вручную передать конкретный путь к файлу обучения через аргумент: `python training/train.py --data "путь_к_файлу.csv"`.

После обучения новые `.pkl`-файлы будут сохранены в папку `models/`.

### 4. Сравнение моделей и анализ ошибок
- **Сравнение моделей**: Оценка точности различных классификаторов (SVC, Naive Bayes, Logistic Regression) с сохранением результатов в `models/experiments/`:
  ```bash
  python -m training.compare_models
  ```
- **Анализ ошибок**: Сбор неверно классифицированных примеров (FP, FN) для последующего тюнинга данных:
  ```bash
  python -m training.error_analysis
  ```

---

## База данных

В проекте используются следующие таблицы:

| Таблица | Что хранит |
|---|---|
| `users` | пользователи, email, хеш пароля, статус активности |
| `prediction_history` | история запросов `/predict` и `/predict/batch` |
| `feedback` | исправления пользователя по предсказаниям |
| `model_versions` | версии ML-моделей, задел под управление моделями |
| `match_history` | история сравнений резюме и вакансий |


- при удалении пользователя его история удаляется каскадно.

---

## Кэширование, rate limiting и отказоустойчивость

### Кэш предсказаний
Если пользователь отправляет одинаковый текст на той же версии модели, сервис не пересчитывает ML-предсказание заново, а берёт результат из Redis.

### Rate limiting
Rate limiting ограничивает количество запросов пользователя за заданный промежуток времени. По умолчанию:
```env
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```
То есть один пользователь может сделать до 100 запросов в минуту.

### Отказоустойчивость (Resilience)
Взаимодействие с Redis полностью отказоустойчиво. Если сервер Redis по какой-то причине недоступен (например, при локальном запуске без Docker-контейнеров):
- Логируется предупреждение в консоли.
- API продолжает стабильно работать, просто пропуская кэширование и проверки лимитов.

---

## Веб-интерфейс (SPA)

В сервис интегрирован современный интерактивный веб-интерфейс в стиле **Dark Glassmorphism**, который раздаётся FastAPI по корневому адресу: `http://localhost:8000/`.

### Возможности интерфейса:
- **Авторизация**: Экран регистрации и входа. JWT-токен сессии сохраняется в `localStorage` браузера для бесшовного обновления страниц.

### Разработка фронтенда:
Папка `static/` примонтирована как Docker Volume. Любые изменения в HTML/CSS/JS применяются в реальном времени в браузере без пересборки контейнеров.

---

## Мониторинг

Сервис отдаёт Prometheus-метрики на эндпоинте:

```text
/metrics
```

Prometheus забирает их по настройке из `monitoring/prometheus.yml`.

Grafana подключается к Prometheus и нужна для визуального мониторинга API: графики запросов, задержек, ошибок, кэша и confidence.

---

## Тесты

Запуск тестов:

```bash
pytest
```
или в докере: 

```bash
docker compose run --rm api pytest -q
```



## Реализовано:

- REST API на FastAPI.
- JWT-аутентификация.
- Регистрация и логин.
- Предсказание категории и уровня текста.
- Извлечение навыков из текста.
- Batch prediction.
- Сравнение резюме и вакансии.
- Расчёт `match_score`.
- Сохранение истории предсказаний.
- Сохранение истории сравнений.
- Feedback по предсказаниям.
- PostgreSQL-модели и репозитории.
- Alembic-миграции.
- Redis-кэш.
- Rate limiting.
- Prometheus-метрики.
- Grafana в Docker Compose.
- Pytest-тесты.
- Dockerfile и docker-compose.yml.

---
