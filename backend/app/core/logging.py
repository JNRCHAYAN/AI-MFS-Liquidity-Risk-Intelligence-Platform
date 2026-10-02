"""Request-scoped logging.

Every log line carries a request ID so a request can be traced end to end
without logging tokens or secrets. See AGENTS.md: log request ID, assessment
ID, model version, duration and error category — never credentials.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

# Populated by middleware for the duration of a request.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Header used by clients and proxies to correlate a request.
REQUEST_ID_HEADER = "X-Request-ID"

_CONFIGURED = False


class RequestIdFilter(logging.Filter):
    """Attaches the current request ID to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        logging.getLogger().setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn installs its own handlers; let them propagate to ours instead.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger."""
    return logging.getLogger(name)
