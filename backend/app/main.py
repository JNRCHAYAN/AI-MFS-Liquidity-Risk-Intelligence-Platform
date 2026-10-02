"""FastAPI application factory.

The app is assembled here and nowhere else, so tests can build an instance
with overridden settings without importing a module-level global.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import (
    FEATURE_SCHEMA_VERSION,
    POLICY_VERSION,
    get_settings,
)
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

logger = get_logger(__name__)

#: Root path for the versioned API.
API_V1_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown.

    Deliberately minimal. The model bundle is *not* loaded here: loading is
    owned by the inference layer, which caches it once per process and reports
    readiness through the health endpoint. Training never runs at startup.
    """
    settings = get_settings()
    logger.info(
        "Starting upay Shield API env=%s feature_schema=%s policy=%s",
        settings.app_env,
        FEATURE_SCHEMA_VERSION,
        POLICY_VERSION,
    )
    yield
    logger.info("Shutting down upay Shield API")


def create_app() -> FastAPI:
    """Build and return the application."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="upay Shield API",
        version="0.1.0",
        summary=(
            "Trust & Risk Intelligence — hackathon prototype. Synthetic data "
            "only; no real transactions."
        ),
        description=(
            "Fraud-analyst decision support: causal feature snapshots, a "
            "trained tabular classifier, a behavioural anomaly score, "
            "time-bounded graph evidence and versioned policy routing.\n\n"
            "Every consequential action is *simulated* and requires an "
            "authorised human analyst."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- Middleware --------------------------------------------------------
    # CORS uses an exact allowlist from configuration. CORS is not
    # authentication: every protected route still verifies the caller.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    # Added last so it runs outermost and every log line, including those from
    # CORS rejection, carries a request ID.
    app.add_middleware(RequestContextMiddleware)

    # --- Errors ------------------------------------------------------------
    register_exception_handlers(app)

    # --- Routes ------------------------------------------------------------
    app.include_router(health_router)
    app.include_router(api_router, prefix=API_V1_PREFIX)

    return app


app = create_app()
