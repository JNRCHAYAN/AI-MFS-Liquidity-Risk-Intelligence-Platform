"""Repositories for the alert queue, cases and the case timeline.

Case updates are the one place optimistic concurrency matters: two analysts
editing the same case must not silently overwrite each other. The ``revision``
column is mapped as SQLAlchemy's ``version_id_col`` (see
``app.models.alert.Case``), and :meth:`CaseRepository.apply_update` turns a
stale write into the typed ``Conflict`` error. Alerts and cases also write
their own audit events in the same transaction, so an action and its audit
record can never diverge.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy import case as sql_case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.exc import StaleDataError

from app.core.errors import Conflict
from app.models.alert import Alert, Case, CaseEvent
from app.models.assessment import Assessment
from app.models.audit import AuditEvent
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AnalystDisposition,
    AuditAction,
    CaseEventType,
    CaseStatus,
    RiskCategory,
)
from app.repositories.base import BaseRepository, UpsertResult, bounded_limit, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec

#: Ranking so severity sorts by meaning (critical first) not alphabetically.
_SEVERITY_RANK = sql_case(
    (Alert.severity == AlertSeverity.CRITICAL, 4),
    (Alert.severity == AlertSeverity.HIGH, 3),
    (Alert.severity == AlertSeverity.MEDIUM, 2),
    else_=1,
)


@dataclass(frozen=True)
class SeverityStatusCount:
    """Alert counts for one (severity, status) pair."""

    severity: AlertSeverity
    status: AlertStatus
    count: int


@dataclass(frozen=True)
class CategoryCount:
    """Alert counts for one risk category."""

    category: RiskCategory
    count: int


class AlertRepository(BaseRepository[Alert]):
    """Reads and writes for the analyst alert queue."""

    model = Alert

    SORTABLE: Mapping[str, Any] = {
        "created_at": Alert.created_at,
        "updated_at": Alert.updated_at,
        "id": Alert.id,
        # Semantic severity ordering, not string ordering.
        "severity": _SEVERITY_RANK,
        "status": Alert.status,
    }

    def get_with_assessment(self, alert_id: str) -> Alert | None:
        """Fetch an alert with its assessment and evidence eager-loaded."""
        stmt = (
            select(Alert)
            .where(Alert.id == alert_id)
            .options(
                selectinload(Alert.assessment).selectinload(Assessment.evidence)
            )
        )
        return self.session.scalars(stmt).first()

    def get_for_assessment(self, assessment_id: str) -> Alert | None:
        """Return the alert raised for an assessment, if any."""
        return self.session.scalars(
            select(Alert).where(Alert.assessment_id == assessment_id).limit(1)
        ).first()

    def create(self, alert: Alert) -> UpsertResult[Alert]:
        """Insert an alert idempotently on ``assessment_id``.

        Re-scoring a transaction cannot create a duplicate queue entry.
        """
        existing = self.get_for_assessment(alert.assessment_id)
        if existing is not None:
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(alert)
        except IntegrityError:
            existing = self.get_for_assessment(alert.assessment_id)
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(alert, True)

    def assign(
        self,
        alert_id: str,
        *,
        assigned_to: str,
        actor: str,
        request_id: str | None = None,
    ) -> Alert:
        """Assign an alert to an analyst and record an audit event."""
        alert = self.get_or_raise(alert_id, label="Alert")
        before = {"assigned_to": alert.assigned_to, "status": alert.status.value}
        alert.assigned_to = assigned_to
        alert.status = AlertStatus.ASSIGNED
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.ASSIGNED,
                object_type="alert",
                object_id=alert.id,
                request_id=request_id,
                before_state=before,
                after_state={"assigned_to": assigned_to, "status": alert.status.value},
            )
        )
        self.session.flush()
        return alert

    def set_status(
        self,
        alert_id: str,
        status: AlertStatus,
        *,
        actor: str,
        request_id: str | None = None,
    ) -> Alert:
        """Change an alert's status and record an audit event."""
        alert = self.get_or_raise(alert_id, label="Alert")
        before = alert.status.value
        alert.status = status
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.STATUS_CHANGED,
                object_type="alert",
                object_id=alert.id,
                request_id=request_id,
                before_state={"status": before},
                after_state={"status": status.value},
            )
        )
        self.session.flush()
        return alert

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        category: RiskCategory | None = None,
        assigned_to: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Page[Alert]:
        """Paginated, filtered alert queue."""
        stmt: Select[Any] = select(Alert)
        if status is not None:
            stmt = stmt.where(Alert.status == status)
        if severity is not None:
            stmt = stmt.where(Alert.severity == severity)
        if category is not None:
            stmt = stmt.where(Alert.category == category)
        if assigned_to is not None:
            stmt = stmt.where(Alert.assigned_to == assigned_to)
        if since is not None:
            stmt = stmt.where(Alert.created_at >= ensure_aware(since, name="since"))
        if until is not None:
            stmt = stmt.where(Alert.created_at < ensure_aware(until, name="until"))
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def count_open(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        """Count alerts not yet resolved or dismissed."""
        stmt = (
            select(func.count())
            .select_from(Alert)
            .where(Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.DISMISSED]))
        )
        if start is not None:
            stmt = stmt.where(Alert.created_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Alert.created_at < ensure_aware(end, name="end"))
        return int(self.session.scalar(stmt) or 0)

    def count_by_status_severity(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[SeverityStatusCount]:
        """Alert counts grouped by status and severity (database aggregate)."""
        stmt = select(Alert.severity, Alert.status, func.count()).group_by(
            Alert.severity, Alert.status
        )
        if start is not None:
            stmt = stmt.where(Alert.created_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Alert.created_at < ensure_aware(end, name="end"))
        rows = self.session.execute(stmt).all()
        return [
            SeverityStatusCount(
                severity=row[0],
                status=row[1],
                count=int(row[2]),
            )
            for row in rows
        ]

    def count_by_category(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CategoryCount]:
        """Alert counts grouped by risk category (database aggregate)."""
        stmt = select(Alert.category, func.count()).group_by(Alert.category)
        if start is not None:
            stmt = stmt.where(Alert.created_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Alert.created_at < ensure_aware(end, name="end"))
        rows = self.session.execute(stmt).all()
        return [CategoryCount(category=row[0], count=int(row[1])) for row in rows]


@dataclass(frozen=True)
class OwnerStatusCount:
    """Case counts for one (owner, status) pair."""

    owner: str
    status: CaseStatus
    count: int


class CaseRepository(BaseRepository[Case]):
    """Case lifecycle with optimistic concurrency and audited updates."""

    model = Case

    SORTABLE: Mapping[str, Any] = {
        "updated_at": Case.updated_at,
        "created_at": Case.created_at,
        "id": Case.id,
        "status": Case.status,
    }

    def get_with_events(self, case_id: str) -> Case | None:
        """Fetch a case with its ordered timeline eager-loaded."""
        stmt = (
            select(Case)
            .where(Case.id == case_id)
            .options(selectinload(Case.events))
        )
        return self.session.scalars(stmt).first()

    def create_from_alert(
        self,
        alert_id: str,
        *,
        owner: str,
        actor: str,
        request_id: str | None = None,
    ) -> UpsertResult[Case]:
        """Open a case from an alert, idempotently (one case per alert)."""
        existing = self.session.scalars(
            select(Case).where(Case.alert_id == alert_id).limit(1)
        ).first()
        if existing is not None:
            return UpsertResult(existing, False)

        case = Case(alert_id=alert_id, owner=owner, status=CaseStatus.OPEN)
        try:
            with self.session.begin_nested():
                self.session.add(case)
        except IntegrityError:
            existing = self.session.scalars(
                select(Case).where(Case.alert_id == alert_id).limit(1)
            ).first()
            if existing is None:
                raise
            return UpsertResult(existing, False)

        self.session.add(
            CaseEvent(
                case_id=case.id,
                actor=actor,
                event_type=CaseEventType.CREATED,
                event_metadata={"owner": owner},
            )
        )
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.CREATED,
                object_type="case",
                object_id=case.id,
                request_id=request_id,
                after_state={"alert_id": alert_id, "owner": owner},
            )
        )
        self.session.flush()
        return UpsertResult(case, True)

    def apply_update(
        self,
        case_id: str,
        *,
        expected_revision: int,
        actor: str,
        request_id: str | None = None,
        status: CaseStatus | None = None,
        analyst_disposition: AnalystDisposition | None = None,
        resolution_note: str | None = None,
        event_type: CaseEventType = CaseEventType.STATUS_CHANGED,
    ) -> Case:
        """Apply an update guarded by an expected revision.

        Raises:
            Conflict: if ``expected_revision`` does not match the stored
                revision (the case was changed by someone else). The current
                revision is returned in the error details.
        """
        case = self.get_or_raise(case_id, label="Case")
        if case.revision != expected_revision:
            raise Conflict(
                "Case was modified by another session; reload and retry.",
                details={
                    "case_id": case.id,
                    "expected_revision": expected_revision,
                    "current_revision": case.revision,
                },
            )

        before = {
            "status": case.status.value,
            "analyst_disposition": (
                case.analyst_disposition.value if case.analyst_disposition else None
            ),
        }
        if status is not None:
            case.status = status
        if analyst_disposition is not None:
            case.analyst_disposition = analyst_disposition
        if resolution_note is not None:
            case.resolution_note = resolution_note

        try:
            self.session.flush()
        except StaleDataError as exc:
            # A concurrent update won the race between our check and the write.
            raise Conflict(
                "Case was modified by another session; reload and retry.",
                details={"case_id": case_id},
            ) from exc

        after = {
            "status": case.status.value,
            "analyst_disposition": (
                case.analyst_disposition.value if case.analyst_disposition else None
            ),
        }
        self.session.add(
            CaseEvent(
                case_id=case.id,
                actor=actor,
                event_type=event_type,
                event_metadata={"before": before, "after": after},
            )
        )
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.UPDATED,
                object_type="case",
                object_id=case.id,
                request_id=request_id,
                before_state=before,
                after_state=after,
            )
        )
        self.session.flush()
        return case

    def add_note(
        self,
        case_id: str,
        *,
        actor: str,
        note: str,
        request_id: str | None = None,
    ) -> CaseEvent:
        """Append an analyst note to the case timeline."""
        return self.add_event(
            case_id,
            actor=actor,
            event_type=CaseEventType.NOTE_ADDED,
            event_metadata={"note": note},
            request_id=request_id,
        )

    def add_event(
        self,
        case_id: str,
        *,
        actor: str,
        event_type: CaseEventType,
        event_metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
        audit_action: AuditAction | None = None,
    ) -> CaseEvent:
        """Append a timeline event (and optionally an audit event)."""
        self.get_or_raise(case_id, label="Case")
        event = CaseEvent(
            case_id=case_id,
            actor=actor,
            event_type=event_type,
            event_metadata=event_metadata,
        )
        self.session.add(event)
        if audit_action is not None:
            self.session.add(
                AuditEvent(
                    actor=actor,
                    action=audit_action,
                    object_type="case",
                    object_id=case_id,
                    request_id=request_id,
                    after_state=event_metadata,
                )
            )
        self.session.flush()
        return event

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        owner: str | None = None,
        status: CaseStatus | None = None,
    ) -> Page[Case]:
        """Paginated, filtered case list (ownership is a first-class filter)."""
        stmt: Select[Any] = select(Case)
        if owner is not None:
            stmt = stmt.where(Case.owner == owner)
        if status is not None:
            stmt = stmt.where(Case.status == status)
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def count_by_owner_status(self) -> list[OwnerStatusCount]:
        """Case counts grouped by owner and status (database aggregate)."""
        rows = self.session.execute(
            select(Case.owner, Case.status, func.count()).group_by(
                Case.owner, Case.status
            )
        ).all()
        return [
            OwnerStatusCount(owner=row[0], status=row[1], count=int(row[2]))
            for row in rows
        ]

    def count_reviewed(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        """Count cases that reached a terminal review state."""
        stmt = select(func.count()).select_from(Case).where(
            Case.status.in_([CaseStatus.RESOLVED, CaseStatus.CLOSED])
        )
        if start is not None:
            stmt = stmt.where(Case.updated_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Case.updated_at < ensure_aware(end, name="end"))
        return int(self.session.scalar(stmt) or 0)


class CaseEventRepository(BaseRepository[CaseEvent]):
    """Reads for the append-only case timeline."""

    model = CaseEvent

    SORTABLE: Mapping[str, Any] = {
        "timestamp": CaseEvent.timestamp,
        "id": CaseEvent.id,
    }

    def list_for_case(
        self,
        case_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[CaseEvent]:
        """Timeline for a case, oldest first, bounded and deterministic."""
        bounded = bounded_limit(limit, default=100, maximum=500)
        return list(
            self.session.scalars(
                select(CaseEvent)
                .where(CaseEvent.case_id == case_id)
                .order_by(CaseEvent.timestamp.asc(), CaseEvent.id.asc())
                .limit(bounded)
                .offset(offset)
            ).all()
        )

    def add(self, event: CaseEvent) -> CaseEvent:
        """Stage a single timeline event."""
        self.session.add(event)
        self.session.flush()
        return event
