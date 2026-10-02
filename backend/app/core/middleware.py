"""HTTP middleware.

Currently one concern: request correlation. Every request gets an ID that is
attached to every log line and echoed back to the client, so a report from a
user can be traced to a specific log record without logging anything sensitive.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import REQUEST_ID_HEADER, get_logger, request_id_ctx

logger = get_logger(__name__)

#: Maximum accepted length of a client-supplied request ID. A client-supplied
#: value is untrusted input: it is bounded and stripped of control characters
#: before it reaches the logs.
_MAX_REQUEST_ID_LEN = 128


def _sanitise_request_id(raw: str | None) -> str | None:
    """Return a safe client-supplied request ID, or None to generate one."""
    if not raw:
        return None
    cleaned = "".join(ch for ch in raw if ch.isprintable() and ch not in "\r\n")
    cleaned = cleaned.strip()[:_MAX_REQUEST_ID_LEN]
    return cleaned or None


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign a request ID and log one line per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _sanitise_request_id(
            request.headers.get(REQUEST_ID_HEADER)
        ) or uuid.uuid4().hex
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Log the category and correlation ID, never the payload or a
            # stack trace, then let the registered handler shape the response.
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "Unhandled error %s %s duration_ms=%.1f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "%s %s -> %d duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
