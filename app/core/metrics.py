from prometheus_client import Counter, Histogram

prediction_count = Counter(
    "prediction_count_total", "Общее количество выполненных предсказаний", ["category", "level"]
)

prediction_latency = Histogram(
    "prediction_latency_seconds", "Время выполнения предсказания в секундах"
)

cache_hits = Counter("cache_hits_total", "Количество попаданий в кэш предсказаний")
cache_misses = Counter("cache_misses_total", "Количество промахов кэша предсказаний")

prediction_errors = Counter("prediction_errors_total", "Количество ошибок при предсказании")

model_confidence = Histogram(
    "model_confidence", "Распределение значений confidence предсказаний"
)
