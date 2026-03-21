import logging
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

from app.analysis_ai.router import router as analysis_router
from app.reports.router import router as reports_router
from app.suggestions.router import router as suggestions_router

# Global logging configuration
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(Path(settings.LOG_FILENAME), mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Suppress noisy library logs
for logger_name in ("httpx", "httpcore"):
    logging.getLogger(logger_name).setLevel(logging.WARNING)

app = FastAPI(title="Safecurity AI-EDR Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(suggestions_router)


@app.get("/api/health-check", tags=["System"])
async def health_check():
    return {"status": "online"}
