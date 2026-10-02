"""Server-side aggregate queries for the dashboard.

The dashboard must never fetch every transaction to compute a KPI in Python.
Every method here issues a ``COUNT`` / ``GROUP BY`` query and returns a small
immutable dataclass.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case as sql_case
from sqlalchemy import func, select

from app.core.config import BUSINESS_TIMEZONE
from app.models.alert import Alert, Case
from app.models.assessment import Assessment
from app.models.enums import AlertSeverity, AlertStatus, CaseStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository, bounded_limit, ensure_aware

_SEVERITY_RANK = sql_case(
    (Alert.severity == AlertSeverity.CRITICAL, 4),
    (Alert.severity == AlertSeverity.HIGH, 3),
    (Alert.severity == AlertSeverity.MEDIUM, 2),
    else_=1,
)
_TERMINAL_ALERT_STATUSES = (AlertStatus.RESOLVED, AlertStatus.DISMISSED)


@dataclass(frozen=True)
class DashboardOverview:
    """Headline KPIs for a time window."""

    scored_transactions: int
    total_alerts: int
    open_alerts: int
    alert_rate: float | None
    reviewed_cases: int


@dataclass(frozen=True)
class DayCount:
    """Per-day transaction and alert counts (business timezone)."""

    day: datetime
    transactions: int
    alerts: int


@dataclass(frozen=True)
class TypeCount:
    """Per-type transaction count and amount volume."""

    transaction_type: TransactionType
    count: int
    total_poisha: int


class DashboardRepository(BaseRepository[Transaction]):
    """Aggregate reads used by the overview dashboard."""

    model = Transaction

    def overview(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> DashboardOverview:
        """Compute headline KPIs with four bounded aggregate queries."""
        lower = ensure_aware(start, name="start") if start else None
        upper = ensure_aware(end, name="end") if end else None

        scored_stmt = select(
            func.count(func.distinct(Assessment.transaction_id))
        ).select_from(Assessment)
        total_alerts_stmt = select(func.count()).select_from(Alert)
        open_alerts_stmt = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.status.notin_(_TERMINAL_ALERT_STATUSES))
        )
        reviewed_stmt = (
            select(func.count())
            .select_from(Case)
            .where(Case.status.in_([CaseStatus.RESOLVED, CaseStatus.CLOSED]))
        )
        if lower is not None:
            scored_stmt = scored_stmt.where(Assessment.assessed_at >= lower)
            total_alerts_stmt = total_alerts_stmt.where(Alert.created_at >= lower)
            open_alerts_stmt = open_alerts_stmt.where(Alert.created_at >= lower)
            reviewed_stmt = reviewed_stmt.where(Case.updated_at >= lower)
        if upper is not None:
            scored_stmt = scored_stmt.where(Assessment.assessed_at < upper)
            total_alerts_stmt = total_alerts_stmt.where(Alert.created_at < upper)
            open_alerts_stmt = open_alerts_stmt.where(Alert.created_at < upper)
            reviewed_stmt = reviewed_stmt.where(Case.updated_at < upper)

        scored = int(self.session.scalar(scored_stmt) or 0)
        total_alerts = int(self.session.scalar(total_alerts_stmt) or 0)
        open_alerts = int(self.session.scalar(open_alerts_stmt) or 0)
        reviewed = int(self.session.scalar(reviewed_stmt) or 0)
        alert_rate = (total_alerts / scored) if scored > 0 else None
        return DashboardOverview(
            scored_transactions=scored,
            total_alerts=total_alerts,
            open_alerts=open_alerts,
            alert_rate=alert_rate,
            reviewed_cases=reviewed,
        )

    def counts_by_day(
        self,
        *,
        start: datetime,
        end: datetime,
        timezone: str = BUSINESS_TIMEZONE,
    ) -> list[DayCount]:
        """Transaction and alert counts per business-timezone day.

        The day boundary is derived in the configured business timezone
        (Asia/Dhaka by default), matching how behavioural features are derived,
        rather than in UTC.
        """
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(end, name="end")
        txn_day = func.date_trunc(
            "day", func.timezone(timezone, Transaction.timestamp)
        ).label("day")
        alert_day = func.date_trunc(
            "day", func.timezone(timezone, Alert.created_at)
        ).label("day")

        txn_rows = self.session.execute(
            select(txn_day, func.count())
            .where(Transaction.timestamp >= lower, Transaction.timestamp < upper)
            .group_by(txn_day)
            .order_by(txn_day)
        ).all()
        alert_rows = self.session.execute(
            select(alert_day, func.count())
            .where(Alert.created_at >= lower, Alert.created_at < upper)
            .group_by(alert_day)
            .order_by(alert_day)
        ).all()

        alerts_by_day = {row[0]: int(row[1]) for row in alert_rows}
        days = {row[0] for row in txn_rows} | set(alerts_by_day)
        transactions_by_day = {row[0]: int(row[1]) for row in txn_rows}
        return [
            DayCount(
                day=day,
                transactions=transactions_by_day.get(day, 0),
                alerts=alerts_by_day.get(day, 0),
            )
            for day in sorted(days)
        ]

    def counts_by_type(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[TypeCount]:
        """Transaction count and amount volume grouped by type."""
        stmt = select(
            Transaction.type,
            func.count(),
            func.coalesce(func.sum(Transaction.amount_poisha), 0),
        ).group_by(Transaction.type)
        if start is not None:
            stmt = stmt.where(Transaction.timestamp >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Transaction.timestamp < ensure_aware(end, name="end"))
        rows = self.session.execute(stmt).all()
        return [
            TypeCount(
                transaction_type=row[0],
                count=int(row[1]),
                total_poisha=int(row[2]),
            )
            for row in rows
        ]

    def top_open_alerts(self, *, limit: int = 10) -> Sequence[Alert]:
        """Most urgent open alerts, bounded, semantic severity ordering."""
        bounded = bounded_limit(limit, default=10, maximum=50)
        return list(
            self.session.scalars(
                select(Alert)
                .where(Alert.status.notin_(_TERMINAL_ALERT_STATUSES))
                .order_by(_SEVERITY_RANK.desc(), Alert.created_at.desc(), Alert.id.desc())
                .limit(bounded)
            ).all()
        )
