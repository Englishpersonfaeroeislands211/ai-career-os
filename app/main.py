from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.llm import router as llm_router
from app.api.routes import router
from app.api.settings import router as settings_router
from app.config import settings
from app.db.session import engine
from app.logging_config import RequestLoggingMiddleware, get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down — disposing DB engine")
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")
app.include_router(llm_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
