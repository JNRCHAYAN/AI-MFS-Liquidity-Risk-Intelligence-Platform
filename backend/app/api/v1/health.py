"""Health and readiness endpoints.

These are mounted at the application root (``/health/...``), not under
``/api/v1``, so that infrastructure probes do not depend on API versioning.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.config import FEATURE_SCHEMA_VERSION, POLICY_VERSION, get_settings
from app.core.readiness import DependencyStatus, run_readiness_checks

router = APIRouter(tags=["health"])


@router.get(
    "/health/live",
    summary="Liveness probe",
    description=(
        "Reports that the process is alive and serving. Deliberately cheap and "
        "independent of the database or model bundle, so an unhealthy "
        "dependency does not cause the platform to restart a working process."
    ),
)
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get(
    "/health/ready",
    summary="Readiness probe",
    description=(
        "Reports whether every required dependency is usable. Returns 503 with "
        "a per-dependency breakdown when the database or model bundle is "
        "missing or invalid. Never reports ready in order to look healthy."
    ),
)
async def readiness(response: Response) -> dict[str, object]:
    ready, reports = run_readiness_checks()

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    settings = get_settings()
    return {
        "status": "ready" if ready else "not_ready",
        "environment": settings.app_env,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "policy_version": POLICY_VERSION,
        "dependencies": [report.as_dict() for report in reports],
        # Surfaced so an operator can see degraded-but-optional capability,
        # e.g. the LLM being absent, without that failing readiness.
        "degraded": [
            report.name
            for report in reports
            if report.status is DependencyStatus.DEGRADED
        ],
    }
