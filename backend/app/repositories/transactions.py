"""Transaction repository — the ledger's only SQL surface.

The feature engine depends on one method in particular:
:meth:`TransactionRepository.events_before`. Its causality contract (strictly
before ``as_of``, deterministic tie-breaking) is what keeps training and online
inference identical. Everything else here is bounded, aggregate or paginated;
nothing fetches the whole ledger to compute a statistic in Python.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import Select, delete, distinct, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.errors import ValidationFailed
from app.models.assessment import Assessment
from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository, UpsertResult, bounded_limit, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec

#: Hard cap on causal reads. Large enough for the 24h/30d feature windows,
#: small enough that a mis-specified window cannot exhaust memory.
MAX_CAUSAL_ROWS = 2000


class Direction(StrEnum):
    """Which side of a transaction an entity is on."""

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    EITHER = "either"


@dataclass(frozen=True)
class TransactionFilters:
    """Optional filters for the paginated transaction list."""

    sender_id: str | None = None
    receiver_id: str | None = None
    entity_id: str | None = None
    transaction_type: TransactionType | None = None
    status: TransactionStatus | None = None
    scenario_run_id: str | None = None
    min_amount_poisha: int | None = None
    max_amount_poisha: int | None = None
    since: datetime | None = None
    until: datetime | None = None


@dataclass(frozen=True)
class TransactionAmountStats:
    """Aggregate statistics over a bounded set of prior transactions.

    Median is computed in the database with ``percentile_cont(0.5)`` so large
    histories never have to be materialised in Python. Fields are ``None`` when
    there are no matching rows (or, for stddev, fewer than two).
    """

    count: int
    total_poisha: int
    mean_poisha: float | None
    median_poisha: float | None
    std_poisha: float | None
    min_poisha: int | None
    max_poisha: int | None


class TransactionRepository(BaseRepository[Transaction]):
    """All reads and writes for the transaction ledger."""

    model = Transaction

    SORTABLE: Mapping[str, Any] = {
        "timestamp": Transaction.timestamp,
        "id": Transaction.id,
        "amount_poisha": Transaction.amount_poisha,
        "created_at": Transaction.created_at,
    }

    # --- Point access ------------------------------------------------------
    def get_with_assessment(self, transaction_id: str) -> Transaction | None:
        """Fetch a transaction with its assessment and evidence eager-loaded.

        Relationships are ``lazy="raise"``, so the API must call this (or
        otherwise load explicitly) rather than letting a serializer trigger an
        unbounded lazy load.
        """
        stmt = (
            select(Transaction)
            .where(Transaction.id == transaction_id)
            .options(
                selectinload(Transaction.assessment).selectinload(Assessment.evidence)
            )
        )
        return self.session.scalars(stmt).first()

    def exists(self, transaction_id: str) -> bool:
        """Whether a transaction id is already present."""
        return (
            self.session.scalar(
                select(func.count())
                .select_from(Transaction)
                .where(Transaction.id == transaction_id)
            )
            or 0
        ) > 0

    def get_by_idempotency_key(self, key: str) -> Transaction | None:
        """Look up a transaction by the scoring endpoint's idempotency key."""
        return self.session.scalars(
            select(Transaction).where(Transaction.idempotency_key == key).limit(1)
        ).first()

    # --- Writes ------------------------------------------------------------
    def upsert(self, txn: Transaction) -> UpsertResult[Transaction]:
        """Insert a transaction idempotently.

        Deduplicates on the transaction id first, then on the idempotency key,
        and finally relies on a savepoint so a concurrent insert that wins the
        race is returned rather than raising. Safe to call on a replayed event.
        """
        existing = self.get(txn.id)
        if existing is not None:
            return UpsertResult(existing, False)
        if txn.idempotency_key:
            existing = self.get_by_idempotency_key(txn.idempotency_key)
            if existing is not None:
                return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(txn)
        except IntegrityError:
            existing = self.get(txn.id) or (
                self.get_by_idempotency_key(txn.idempotency_key)
                if txn.idempotency_key
                else None
            )
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(txn, True)

    def set_status(
        self,
        transaction_id: str,
        status: TransactionStatus,
    ) -> Transaction | None:
        """Update a transaction's simulated status; ``None`` if absent."""
        txn = self.get(transaction_id)
        if txn is None:
            return None
        txn.status = status
        self.session.flush()
        return txn

    def delete_for_run(self, scenario_run_id: str) -> int:
        """Delete every transaction belonging to one simulation run.

        A scoped reset: it never touches rows from other runs. The database
        cascades to assessments, evidence, alerts, cases and case events; audit
        events have no foreign key and therefore survive.
        """
        result = self.session.execute(
            delete(Transaction).where(Transaction.scenario_run_id == scenario_run_id)
        )
        return int(result.rowcount or 0)

    # --- Causality-critical reads -----------------------------------------
    def events_before(
        self,
        as_of: datetime,
        *,
        sender_id: str | None = None,
        receiver_id: str | None = None,
        entity_id: str | None = None,
        order_desc: bool = True,
        limit: int = 500,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        """Return events **strictly before** ``as_of``.

        .. important::

           This is the feature engine's causal read. Its guarantees are part of
           the feature contract:

           * The predicate is ``timestamp < as_of``. An event at exactly
             ``as_of`` is **excluded** — including the transaction currently
             being scored.
           * Ordering ties on equal timestamps are broken by ``id``, so the
             order is a deterministic total order and training/inference agree.
           * ``as_of`` must be timezone-aware; a naive value is rejected.

        Provide at most one of ``sender_id`` (outgoing only), ``receiver_id``
        (incoming only) or ``entity_id`` (either side). Provide none to read
        all events before ``as_of`` (still bounded by ``limit``).

        Returns rows ordered newest-first when ``order_desc`` is true.
        """
        moment = ensure_aware(as_of, name="as_of")
        bounded = bounded_limit(
            limit, default=500, maximum=MAX_CAUSAL_ROWS, name="limit"
        )
        provided = [
            name
            for name, value in (
                ("sender_id", sender_id),
                ("receiver_id", receiver_id),
                ("entity_id", entity_id),
            )
            if value is not None
        ]
        if len(provided) > 1:
            raise ValidationFailed(
                "Provide at most one of sender_id, receiver_id or entity_id.",
                details={"fields": provided},
            )

        stmt = select(Transaction).where(Transaction.timestamp < moment)
        if sender_id is not None:
            stmt = stmt.where(Transaction.sender_id == sender_id)
        elif receiver_id is not None:
            stmt = stmt.where(Transaction.receiver_id == receiver_id)
        elif entity_id is not None:
            stmt = stmt.where(
                (Transaction.sender_id == entity_id)
                | (Transaction.receiver_id == entity_id)
            )

        if order_desc:
            stmt = stmt.order_by(Transaction.timestamp.desc(), Transaction.id.desc())
        else:
            stmt = stmt.order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        return list(
            self.session.scalars(stmt.limit(bounded).offset(offset)).all()
        )

    def events_in_window(
        self,
        entity_id: str,
        *,
        direction: Direction = Direction.OUTGOING,
        start: datetime,
        end: datetime,
        limit: int = 500,
        offset: int = 0,
    ) -> Sequence[Transaction]:
        """Return events in the half-open interval ``[start, end)`` for an entity.

        Always bounded. ``end`` is exclusive for the same causal reason as
        :meth:`events_before`.
        """
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(end, name="end")
        if upper < lower:
            raise ValidationFailed("end must not be earlier than start.")
        bounded = bounded_limit(limit, default=500, maximum=MAX_CAUSAL_ROWS)

        stmt = select(Transaction).where(
            Transaction.timestamp >= lower,
            Transaction.timestamp < upper,
        )
        if direction is Direction.OUTGOING:
            stmt = stmt.where(Transaction.sender_id == entity_id)
        elif direction is Direction.INCOMING:
            stmt = stmt.where(Transaction.receiver_id == entity_id)
        else:
            stmt = stmt.where(
                (Transaction.sender_id == entity_id)
                | (Transaction.receiver_id == entity_id)
            )
        stmt = stmt.order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        return list(self.session.scalars(stmt.limit(bounded).offset(offset)).all())

    # --- Bounded aggregates (never fetch-then-count in Python) -------------
    def _direction_filter(
        self,
        stmt: Select[Any],
        entity_id: str,
        direction: Direction,
    ) -> Select[Any]:
        if direction is Direction.OUTGOING:
            return stmt.where(Transaction.sender_id == entity_id)
        if direction is Direction.INCOMING:
            return stmt.where(Transaction.receiver_id == entity_id)
        return stmt.where(
            (Transaction.sender_id == entity_id)
            | (Transaction.receiver_id == entity_id)
        )

    def count_in_window(
        self,
        entity_id: str,
        *,
        direction: Direction,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count an entity's transactions in ``[start, end)`` in the database."""
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(end, name="end")
        stmt = select(func.count()).select_from(Transaction).where(
            Transaction.timestamp >= lower,
            Transaction.timestamp < upper,
        )
        stmt = self._direction_filter(stmt, entity_id, direction)
        return int(self.session.scalar(stmt) or 0)

    def sum_amount_in_window(
        self,
        entity_id: str,
        *,
        direction: Direction,
        start: datetime,
        end: datetime,
    ) -> int:
        """Sum amounts (poisha) for an entity in ``[start, end)``."""
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(end, name="end")
        stmt = select(func.coalesce(func.sum(Transaction.amount_poisha), 0)).where(
            Transaction.timestamp >= lower,
            Transaction.timestamp < upper,
        )
        stmt = self._direction_filter(stmt, entity_id, direction)
        return int(self.session.scalar(stmt) or 0)

    def distinct_counterparties_in_window(
        self,
        entity_id: str,
        *,
        direction: Direction,
        start: datetime,
        end: datetime,
    ) -> int:
        """Count distinct counterparties an entity dealt with in ``[start, end)``."""
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(end, name="end")
        counterparty = (
            Transaction.receiver_id
            if direction is Direction.OUTGOING
            else Transaction.sender_id
        )
        stmt = select(func.count(distinct(counterparty))).where(
            Transaction.timestamp >= lower,
            Transaction.timestamp < upper,
        )
        if direction is Direction.EITHER:
            # Distinct counterparties on either side; the CASE keeps it a
            # single bounded aggregate rather than fetching rows.
            counterparty = func.coalesce(
                func.nullif(Transaction.sender_id, entity_id),
                Transaction.receiver_id,
            )
            stmt = select(func.count(distinct(counterparty))).where(
                Transaction.timestamp >= lower,
                Transaction.timestamp < upper,
                (Transaction.sender_id == entity_id)
                | (Transaction.receiver_id == entity_id),
            )
        else:
            stmt = self._direction_filter(stmt, entity_id, direction)
        return int(self.session.scalar(stmt) or 0)

    def amount_stats_before(
        self,
        entity_id: str,
        *,
        before: datetime,
        window_start: datetime | None = None,
        direction: Direction = Direction.OUTGOING,
    ) -> TransactionAmountStats:
        """Prior-only amount statistics for one entity.

        Uses events in ``[window_start, before)`` (open-ended in the past when
        ``window_start`` is ``None``). Computed entirely in PostgreSQL,
        including the median via ``percentile_cont``.
        """
        upper = ensure_aware(before, name="before")
        conditions = [Transaction.timestamp < upper]
        if window_start is not None:
            conditions.append(
                Transaction.timestamp >= ensure_aware(window_start, name="window_start")
            )
        amount = Transaction.amount_poisha
        stmt = select(
            func.count(),
            func.coalesce(func.sum(amount), 0),
            func.avg(amount),
            func.percentile_cont(0.5).within_group(amount.asc()),
            func.stddev_pop(amount),
            func.min(amount),
            func.max(amount),
        ).where(*conditions)
        stmt = self._direction_filter(stmt, entity_id, direction)
        row = self.session.execute(stmt).one()
        return TransactionAmountStats(
            count=int(row[0] or 0),
            total_poisha=int(row[1] or 0),
            mean_poisha=float(row[2]) if row[2] is not None else None,
            median_poisha=float(row[3]) if row[3] is not None else None,
            std_poisha=float(row[4]) if row[4] is not None else None,
            min_poisha=int(row[5]) if row[5] is not None else None,
            max_poisha=int(row[6]) if row[6] is not None else None,
        )

    def has_prior_pair(self, sender_id: str, receiver_id: str, *, before: datetime) -> bool:
        """Whether ``sender_id`` ever paid ``receiver_id`` strictly before ``before``.

        Backs the ``recipient_is_new`` feature with a single bounded existence
        query instead of loading history.
        """
        upper = ensure_aware(before, name="before")
        found = self.session.scalar(
            select(func.count())
            .select_from(Transaction)
            .where(
                Transaction.sender_id == sender_id,
                Transaction.receiver_id == receiver_id,
                Transaction.timestamp < upper,
            )
            .limit(1)
        )
        return bool(found)

    # --- Paginated listing -------------------------------------------------
    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        filters: TransactionFilters | None = None,
    ) -> Page[Transaction]:
        """Paginated, filtered transaction list with stable total ordering."""
        applied = filters or TransactionFilters()
        stmt: Select[Any] = select(Transaction)
        if applied.sender_id is not None:
            stmt = stmt.where(Transaction.sender_id == applied.sender_id)
        if applied.receiver_id is not None:
            stmt = stmt.where(Transaction.receiver_id == applied.receiver_id)
        if applied.entity_id is not None:
            stmt = stmt.where(
                (Transaction.sender_id == applied.entity_id)
                | (Transaction.receiver_id == applied.entity_id)
            )
        if applied.transaction_type is not None:
            stmt = stmt.where(Transaction.type == applied.transaction_type)
        if applied.status is not None:
            stmt = stmt.where(Transaction.status == applied.status)
        if applied.scenario_run_id is not None:
            stmt = stmt.where(Transaction.scenario_run_id == applied.scenario_run_id)
        if applied.min_amount_poisha is not None:
            stmt = stmt.where(Transaction.amount_poisha >= applied.min_amount_poisha)
        if applied.max_amount_poisha is not None:
            stmt = stmt.where(Transaction.amount_poisha <= applied.max_amount_poisha)
        if applied.since is not None:
            stmt = stmt.where(
                Transaction.timestamp >= ensure_aware(applied.since, name="since")
            )
        if applied.until is not None:
            stmt = stmt.where(
                Transaction.timestamp < ensure_aware(applied.until, name="until")
            )
        return self._paginate(stmt, params, sort, self.SORTABLE)
