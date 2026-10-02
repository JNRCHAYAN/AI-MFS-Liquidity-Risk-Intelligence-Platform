"""Declarative base, identifier scheme and shared column helpers.

This module is the root of the ORM. Every table class inherits from
:class:`Base` so that ``Base.metadata`` is the single registry Alembic
autogenerates from. :mod:`app.models` imports every model module for that
reason; do not remove those imports.

Conventions enforced here (see AGENTS.md and docs/architecture.md section 5):

* **Money is integer poisha.** Money columns use ``BigInteger``; never a
  binary float and never ``Numeric(asdecimal=False)``.
* **Timestamps are timezone-aware UTC.** Columns use
  ``DateTime(timezone=True)`` and application defaults use
  :func:`utcnow`. Naive datetimes are never stored.
* **Stable, typed identifiers.** Every row has a string primary key with a
  type prefix (``txn_``, ``asm_``, ...). The prefix makes an ID recognisable
  in logs and evidence lists, and equals the natural key the simulator or
  service supplies when it wants deterministic replay.
* **Deterministic constraint names.** A naming convention is applied so that
  index/constraint names are stable across migrations and test databases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

#: Deterministic names for every indexed constraint. Without this, PostgreSQL
#: invents names that differ between environments and migrations drift.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

#: Maximum length of a prefixed string identifier. ``prefix`` + 32 hex chars
#: fits comfortably; longer imported identifiers are truncated by the caller.
ID_LENGTH = 64

# Prefixes for the identifier scheme. Kept together so the scheme is obvious
# and consistent across tables, repositories and evidence references.
ENTITY_ID_PREFIX = "ent"
DEVICE_ID_PREFIX = "dev"
TRANSACTION_ID_PREFIX = "txn"
ASSESSMENT_ID_PREFIX = "asm"
EVIDENCE_ID_PREFIX = "evd"
ALERT_ID_PREFIX = "alt"
CASE_ID_PREFIX = "case"
CASE_EVENT_ID_PREFIX = "cev"
AUDIT_ID_PREFIX = "aud"
SIMULATION_RUN_ID_PREFIX = "run"
MODEL_VERSION_ID_PREFIX = "mdl"
SCENARIO_TRUTH_ID_PREFIX = "trh"


class Base(DeclarativeBase):
    """Declarative base for every upay Shield table."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    ``datetime.utcnow()`` is deprecated and returns a naive value; this
    helper is the only supported way to obtain "now" for an ORM default.
    """
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    """Return a new identifier of the form ``<prefix>_<32 hex chars>``.

    Random by design. Callers that need reproducible identifiers (the
    simulator) pass an explicit value instead of relying on this default.
    """
    return f"{prefix}_{uuid4().hex}"


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` in UTC.

    ``updated_at`` is refreshed by SQLAlchemy on every ORM update rather than
    by a database trigger, so it stays correct as long as writes go through
    the repositories (which is the only place SQL is allowed).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )
