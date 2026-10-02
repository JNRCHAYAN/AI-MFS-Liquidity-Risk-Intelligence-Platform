"""Shared repository plumbing.

Repositories are the *only* place SQL is written (AGENTS.md, architecture
section 4). This base class centralises the mandatory behaviours every list
query must have: bounded pagination, a whitelist of sortable columns, and a
unique tie-breaker appended to every sort so pagination is stable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.errors import NotFound, ValidationFailed
from app.models.base import Base
from app.repositories.pagination import Page, PageParams, SortOrder, SortSpec

ModelT = TypeVar("ModelT", bound=Base)

#: Rows per INSERT statement in a bulk load. Keeps the parameter count well
#: under PostgreSQL's 65535 bind-parameter limit.
DEFAULT_BULK_CHUNK = 1000


def orm_insert_values(obj: Base) -> dict[str, Any]:
    """Return a column-keyed dict for one ORM object, for a core INSERT.

    Keys whose value is ``None`` on a column that has a Python or server
    default are omitted, so the default still applies (a naive
    ``getattr``-every-column copy would write NULL and defeat ``now()``).
    """
    values: dict[str, Any] = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.key)
        if value is None and (
            column.default is not None or column.server_default is not None
        ):
            continue
        values[column.key] = value
    return values


@dataclass
class UpsertResult(Generic[ModelT]):
    """Outcome of an idempotent write."""

    obj: ModelT
    #: True when the row was inserted, False when an existing row was reused.
    created: bool


def ensure_aware(value: datetime, *, name: str) -> datetime:
    """Reject naive datetimes and normalise aware values to UTC.

    Naive timestamps are the single most common source of off-by-timezone
    causality bugs in the feature engine, so they are a hard validation error
    rather than an implicit assumption of UTC.
    """
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValidationFailed(
            f"{name} must be a timezone-aware datetime (UTC).",
            details={"field": name},
        )
    return value.astimezone(UTC)


def bounded_limit(
    value: int,
    *,
    default: int,
    maximum: int,
    name: str = "limit",
) -> int:
    """Validate a caller-supplied limit against an explicit range."""
    if value < 1:
        raise ValidationFailed(
            f"{name} must be >= 1.",
            details={"field": name, "value": value},
        )
    if value > maximum:
        raise ValidationFailed(
            f"{name} must be <= {maximum}.",
            details={"field": name, "value": value, "maximum": maximum},
        )
    return value


class BaseRepository(Generic[ModelT]):
    """Base class for aggregate repositories."""

    #: The mapped class this repository manages. Set by every subclass.
    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    # --- Single-row access -------------------------------------------------
    def get(self, pk: str) -> ModelT | None:
        """Return the row with primary key ``pk`` or ``None``."""
        return self.session.get(self.model, pk)

    def get_or_raise(self, pk: str, *, label: str | None = None) -> ModelT:
        """Return the row or raise the typed ``NotFound`` error."""
        obj = self.get(pk)
        if obj is None:
            name = label or self.model.__name__
            raise NotFound(f"{name} {pk!r} was not found.", details={"id": pk})
        return obj

    # --- Writes ------------------------------------------------------------
    def add(self, obj: ModelT) -> ModelT:
        """Stage a new row for insert within the caller's transaction."""
        self.session.add(obj)
        return obj

    def flush(self) -> None:
        """Flush pending work so generated values and constraints apply."""
        self.session.flush()

    def delete(self, obj: ModelT) -> None:
        """Stage a row for deletion."""
        self.session.delete(obj)

    def bulk_insert_ignore_duplicates(
        self,
        rows: Sequence[ModelT],
        *,
        chunk_size: int = DEFAULT_BULK_CHUNK,
    ) -> int:
        """Insert many rows, skipping any that collide on a unique constraint.

        Uses PostgreSQL ``INSERT ... ON CONFLICT DO NOTHING`` with **no**
        conflict target, so a collision on *any* unique index (primary key or
        idempotency key) is skipped rather than raising. This is what makes a
        replayed simulator batch or a retried bulk load safe.

        Returns the number of rows actually inserted. Chunked so a large batch
        cannot exceed the bind-parameter limit.
        """
        if chunk_size < 1:
            raise ValidationFailed("chunk_size must be >= 1.")
        inserted = 0
        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            values = [orm_insert_values(row) for row in chunk]
            if not values:
                continue
            stmt = pg_insert(self.model).on_conflict_do_nothing()
            result = self.session.execute(stmt, values)
            inserted += int(result.rowcount or 0)
        return inserted

    # --- Query helpers -----------------------------------------------------
    def _count(self, stmt: Select[Any]) -> int:
        """Count rows matching an unfiltered/ordered select."""
        total = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        return int(total or 0)

    def _primary_key_column(self) -> Any:
        pk_columns = list(self.model.__table__.primary_key.columns)
        if len(pk_columns) != 1:  # pragma: no cover - defensive invariant
            raise RuntimeError(
                f"{self.model.__name__} must have a single-column primary key "
                "for stable pagination."
            )
        return pk_columns[0]

    def _apply_sort(
        self,
        stmt: Select[Any],
        sort: SortSpec,
        sortable: Mapping[str, Any],
    ) -> Select[Any]:
        """Order by a whitelisted column, then by the primary key.

        The primary-key tie-breaker makes the order total, so paginating a
        column with duplicate values cannot skip or repeat rows.
        """
        column = sortable.get(sort.field)
        if column is None:
            raise ValidationFailed(
                f"Unsupported sort field {sort.field!r}.",
                details={"field": sort.field, "allowed": sorted(sortable)},
            )
        primary = column.desc() if sort.order is SortOrder.DESC else column.asc()
        return stmt.order_by(primary, self._primary_key_column().asc())

    def _paginate(
        self,
        stmt: Select[Any],
        params: PageParams,
        sort: SortSpec,
        sortable: Mapping[str, Any],
    ) -> Page[ModelT]:
        """Apply count, sort and pagination to a filtered select."""
        total = self._count(stmt)
        ordered = self._apply_sort(stmt, sort, sortable)
        rows = list(
            self.session.scalars(
                ordered.limit(params.limit).offset(params.offset)
            ).all()
        )
        return Page(items=rows, total=total, limit=params.limit, offset=params.offset)
