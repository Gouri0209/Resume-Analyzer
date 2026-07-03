"""
AI Resume Analyzer - FastAPI application entrypoint.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume analysis against job descriptions.",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    init_db()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
