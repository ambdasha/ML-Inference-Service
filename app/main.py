from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api import auth, history, predict, match
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.ml.model_loader import load_models

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Загружаем ML-модели заранее, чтобы первый запрос не был медленным
    try:
        load_models()
    except FileNotFoundError as exc:
        logger.warning("ML-модели не загружены при старте: %s", exc)

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Сервис анализа вакансий/резюме: определение направления, навыков и уровня кандидата",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(match.router)
app.include_router(history.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
