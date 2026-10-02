"""Readiness checks for required dependencies.

Readiness is deliberately honest. When a required dependency is missing,
invalid or unreachable, the service reports ``unavailable`` with a specific
reason rather than starting up and later inventing a result. The build plan
requires exactly this: "Health readiness must fail if required
artifacts/schema/checksum are invalid. Return explicit unavailable/degraded
errors instead of inventing scores."

Two probes exist:

* ``/health/live``  — cheap, always 200 while the process is serving.
* ``/health/ready`` — 200 only when every *required* dependency is usable;
  otherwise 503 with a per-dependency breakdown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import FEATURE_SCHEMA_VERSION, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DependencyStatus(StrEnum):
    """Outcome of a single dependency probe."""

    OK = "ok"
    #: Reachable but degraded — the service can still answer some routes.
    DEGRADED = "degraded"
    #: Required and unusable. Readiness must fail.
    UNAVAILABLE = "unavailable"


@dataclass
class DependencyReport:
    """Result of probing one dependency."""

    name: str
    status: DependencyStatus
    detail: str
    required: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "required": self.required,
            "detail": self.detail,
        }
        if self.extra:
            payload["extra"] = self.extra
        return payload


def check_database() -> DependencyReport:
    """Probe the database with a cheap, side-effect-free query."""
    settings = get_settings()
    if not settings.database_url:
        return DependencyReport(
            name="database",
            status=DependencyStatus.UNAVAILABLE,
            detail="DATABASE_URL is not configured.",
            required=True,
        )

    try:
        # Imported lazily so that an unconfigured database surfaces as a
        # readiness failure rather than an import-time crash.
        from app.repositories.session import get_engine

        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # The exception class and a short reason only — never the connection
        # string, which may embed credentials.
        return DependencyReport(
            name="database",
            status=DependencyStatus.UNAVAILABLE,
            detail=f"Database connection failed ({type(exc).__name__}).",
            required=True,
        )
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all for readiness only
        return DependencyReport(
            name="database",
            status=DependencyStatus.UNAVAILABLE,
            detail=f"Database probe failed ({type(exc).__name__}).",
            required=True,
        )

    return DependencyReport(
        name="database",
        status=DependencyStatus.OK,
        detail="Connected.",
        required=True,
    )


def check_model_bundle() -> DependencyReport:
    """Probe the packaged model bundle and its manifest.

    This checks presence, parseability and the recorded feature-schema version.
    It does not load the model: loading is expensive and belongs to the
    inference layer, which caches it once per process.
    """
    settings = get_settings()
    bundle_dir = settings.model_bundle_dir

    if not bundle_dir.exists():
        return DependencyReport(
            name="model_bundle",
            status=DependencyStatus.UNAVAILABLE,
            detail=f"No model bundle at '{bundle_dir}'. Training has not been run.",
            required=True,
            extra={"path": str(bundle_dir)},
        )

    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        return DependencyReport(
            name="model_bundle",
            status=DependencyStatus.UNAVAILABLE,
            detail="Model bundle has no manifest.json.",
            required=True,
            extra={"path": str(bundle_dir)},
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return DependencyReport(
            name="model_bundle",
            status=DependencyStatus.UNAVAILABLE,
            detail=f"Model manifest is unreadable ({type(exc).__name__}).",
            required=True,
        )

    recorded = manifest.get("feature_schema_version")
    if recorded != FEATURE_SCHEMA_VERSION:
        # A mismatch means the artifact was trained against a different feature
        # contract. Scoring with it would silently produce wrong values.
        return DependencyReport(
            name="model_bundle",
            status=DependencyStatus.UNAVAILABLE,
            detail=(
                "Model bundle feature schema version does not match the "
                "running code."
            ),
            required=True,
            extra={
                "artifact_schema_version": recorded,
                "expected_schema_version": FEATURE_SCHEMA_VERSION,
            },
        )

    return DependencyReport(
        name="model_bundle",
        status=DependencyStatus.OK,
        detail="Manifest present and schema version matches.",
        required=True,
        extra={
            "model_version": manifest.get("model_version"),
            "feature_schema_version": recorded,
        },
    )


def check_llm() -> DependencyReport:
    """Probe the *optional* explanation dependency.

    The LLM is never required: the deterministic summary path must work
    without it, so an unconfigured Gemini reports ``degraded``, never
    ``unavailable``.
    """
    settings = get_settings()
    if not settings.llm_enabled:
        return DependencyReport(
            name="llm",
            status=DependencyStatus.DEGRADED,
            detail=(
                "Gemini is not configured. Investigation summaries use the "
                "deterministic path."
            ),
            required=False,
        )
    return DependencyReport(
        name="llm",
        status=DependencyStatus.OK,
        detail="Gemini is configured.",
        required=False,
        extra={"model": settings.gemini_model},
    )


def run_readiness_checks() -> tuple[bool, list[DependencyReport]]:
    """Run every probe.

    Returns:
        A tuple of ``(ready, reports)``. ``ready`` is True only when every
        *required* dependency is OK.
    """
    reports = [check_database(), check_model_bundle(), check_llm()]
    ready = all(
        report.status is DependencyStatus.OK
        for report in reports
        if report.required
    )
    return ready, reports
