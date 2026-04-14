"""Application entrypoint."""

import logging
from fastapi import FastAPI

from app.api.routes import router as api_router
from app.config.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Python Agent Challenge API", version="0.1.0")
app.include_router(api_router)