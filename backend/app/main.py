"""FastAPI application entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_fastn, routes_health
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.integrations.errors import FastnError

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.exception_handler(FastnError)
async def fastn_error_handler(_: Request, exc: FastnError) -> JSONResponse:
    logger.error("fastn error [%s]: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"code": exc.code, "message": exc.message, "hint": exc.hint}},
    )


app.include_router(routes_health.router, prefix="/api")
app.include_router(routes_fastn.router, prefix="/api")
