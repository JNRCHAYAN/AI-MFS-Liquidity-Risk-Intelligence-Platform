"""Typed application error taxonomy.

Every error returned to a client is one of these types. Raw stack traces,
SQL fragments and secret values must never reach an HTTP response.

The shape mirrors RFC 9457 (problem details) closely enough to be useful
without claiming strict compliance:

    {
      "error": {
        "code": "not_found",
        "message": "Transaction was not found.",
        "request_id": "0f2c...",
        "details": {"transaction_id": "txn_123"}
      }
    }
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base class for errors that map to a deliberate HTTP response."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationFailed(AppError):
    """Request payload failed validation.

    FastAPI handles schema-level validation itself; this is for
    domain-level rules that Pydantic cannot express.
    """

    status_code = 422
    code = "validation_failed"


class NotFound(AppError):
    """Requested object does not exist, or is not visible to this caller.

    Deliberately also used for objects that exist but are not accessible to
    the caller, so the API does not leak the existence of other tenants'
    records.
    """

    status_code = 404
    code = "not_found"


class Unauthorized(AppError):
    """No valid credentials were presented."""

    status_code = 401
    code = "unauthorized"


class Forbidden(AppError):
    """Credentials are valid but the role or ownership check failed."""

    status_code = 403
    code = "forbidden"


class Conflict(AppError):
    """The request conflicts with current state (revision, duplicate, idempotency)."""

    status_code = 409
    code = "conflict"


class Unprocessable(AppError):
    """Request is well-formed but cannot be applied in the current state."""

    status_code = 422
    code = "unprocessable"


class RateLimited(AppError):
    """Caller exceeded a documented rate limit."""

    status_code = 429
    code = "rate_limited"


class Unavailable(AppError):
    """A required dependency is missing, invalid or unreachable.

    Used instead of inventing a result. When the model bundle, the feature
    schema or the database is unusable, the service reports degraded rather
    than fabricating a score.
    """

    status_code = 503
    code = "unavailable"
