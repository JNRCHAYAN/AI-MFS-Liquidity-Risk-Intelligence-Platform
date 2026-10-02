"""Exception handlers mapping typed errors to safe HTTP responses.

Two rules govern everything here:

1. A deliberate :class:`~app.core.errors.AppError` is rendered with its own
   code, message and details.
2. Anything else is an internal fault. The client receives a generic message
   and the request ID — never a stack trace, SQL fragment or configuration
   value. The detail goes to the log only.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError
from app.core.logging import get_logger, request_id_ctx

logger = get_logger(__name__)


def _current_request_id() -> str | None:
    """Return the request ID assigned by the middleware.

    Read from the context variable rather than the client's ``X-Request-ID``
    header: the middleware sanitises the inbound value and generates one when
    absent, so the context variable is the value that actually appears in the
    logs and on the response. Reading the raw header here would print ``null``
    whenever the client did not send one.
    """
    return request_id_ctx.get()


def _envelope(
    *,
    code: str,
    message: str,
    request_id: str | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    if details:
        payload["error"]["details"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler to the application."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = _current_request_id()
        # 5xx is a server-side condition worth logging at error level; 4xx is
        # expected client behaviour and does not need a stack trace.
        if exc.status_code >= 500:
            logger.error(
                "AppError %s on %s: %s",
                exc.code,
                request.url.path,
                exc.message,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(
                code=exc.code,
                message=exc.message,
                request_id=request_id,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Surface field locations so a caller can fix the request, but do not
        # echo back the submitted values themselves.
        fields = [
            {
                "location": ".".join(str(part) for part in err.get("loc", ())),
                "reason": err.get("msg", "invalid"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope(
                code="validation_failed",
                message="The request payload failed validation.",
                request_id=_current_request_id(),
                details={"fields": fields},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(
                code="http_error",
                message=str(exc.detail),
                request_id=_current_request_id(),
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals. The request ID is the bridge to the log record.
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                code="internal_error",
                message=(
                    "An internal error occurred. Quote the request ID when "
                    "reporting this."
                ),
                request_id=_current_request_id(),
            ),
        )
