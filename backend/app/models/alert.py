"""Alert queue, investigation cases and the append-only case timeline.

The case is the only aggregate with **optimistic concurrency**: its
``revision`` column is mapped as SQLAlchemy's ``version_id_col``, so an ORM
update automatically becomes ``UPDATE cases SET ..., revision = revision + 1
WHERE id = :id AND revision = :expected``. A concurrent stale write raises
``StaleDataError``, which the repository translates to a typed ``Conflict``.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    ALERT_ID_PREFIX,
    CASE_EVENT_ID_PREFIX,
    CASE_ID_PREFIX,
    ID_LENGTH,
    Base,
    TimestampMixin,
    new_id,
    utcnow,
)
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AnalystDisposition,
    CaseEventType,
    CaseStatus,
    RiskCategory,
    pg_enum,
)

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class Alert(Base):
    """A prioritised item in the analyst queue.

    ``category`` is a hypothesis backed by evidence, never a verdict.
    """

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(ALERT_ID_PREFIX),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[RiskCategory] = mapped_column(
        pg_enum(RiskCategory, name="risk_category"),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        pg_enum(AlertSeverity, name="alert_severity"),
        nullable=False,
    )
    status: Mapped[AlertStatus] = mapped_column(
        pg_enum(AlertStatus, name="alert_status"),
        nullable=False,
        default=AlertStatus.OPEN,
    )
    assigned_to: Mapped[str | None] = mapped_column(String(ID_LENGTH), nullable=True)
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

    assessment: Mapped[Assessment] = relationship(
        back_populates="alert",
        lazy="raise",
    )
    cases: Mapped[list[Case]] = relationship(
        back_populates="alert",
        cascade="all, delete-orphan",
        lazy="raise",
    )

    __table_args__ = (
        # One alert per assessment. Re-scoring the same transaction therefore
        # cannot create a duplicate queue entry.
        UniqueConstraint("assessment_id", name="uq_alerts_assessment_id"),
        # Mandatory alert access path: status/severity/time.
        Index(
            "ix_alerts_status_severity_created_at",
            "status",
            "severity",
            "created_at",
        ),
        Index("ix_alerts_severity_created_at", "severity", "created_at"),
        Index("ix_alerts_status_created_at", "status", "created_at"),
        # Analyst work-queue path.
        Index("ix_alerts_assigned_to_status", "assigned_to", "status"),
        # Category filtering.
        Index("ix_alerts_category_created_at", "category", "created_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Alert {self.id} {self.category}/{self.severity} {self.status}>"


class Case(TimestampMixin, Base):
    """An analyst investigation opened from an alert.

    ``revision`` provides optimistic concurrency for concurrent analysts.
    ``analyst_disposition`` is only set through the audited workflow; it is
    never an input to scoring.
    """

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(CASE_ID_PREFIX),
    )
    alert_id: Mapped[str] = mapped_column(
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: Analyst user identifier that owns the case. The ownership access path.
    owner: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        pg_enum(CaseStatus, name="case_status"),
        nullable=False,
        default=CaseStatus.OPEN,
    )
    analyst_disposition: Mapped[AnalystDisposition | None] = mapped_column(
        pg_enum(AnalystDisposition, name="analyst_disposition"),
        nullable=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Optimistic concurrency version. Managed by SQLAlchemy via
    #: ``__mapper_args__``; never assign to it directly.
    revision: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
    )

    alert: Mapped[Alert] = relationship(back_populates="cases", lazy="raise")
    events: Mapped[list[CaseEvent]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseEvent.timestamp",
        lazy="raise",
    )

    __mapper_args__ = {
        "version_id_col": revision,
        "version_id_generator": lambda version: (version or 0) + 1,
    }

    __table_args__ = (
        # One case per alert keeps case creation idempotent.
        UniqueConstraint("alert_id", name="uq_cases_alert_id"),
        # Mandatory case-ownership access path.
        Index("ix_cases_owner_status", "owner", "status"),
        Index("ix_cases_owner_updated_at", "owner", "updated_at"),
        Index("ix_cases_status_updated_at", "status", "updated_at"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Case {self.id} owner={self.owner} status={self.status} "
            f"rev={self.revision}>"
        )


class CaseEvent(Base):
    """Append-only timeline entry for a case.

    ``metadata`` is a reserved attribute name on a declarative class, so the
    Python attribute is ``event_metadata`` mapped explicitly to the column
    ``metadata``.
    """

    __tablename__ = "case_events"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(CASE_EVENT_ID_PREFIX),
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: Analyst or system identity that produced the event.
    actor: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    event_type: Mapped[CaseEventType] = mapped_column(
        pg_enum(CaseEventType, name="case_event_type"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    case: Mapped[Case] = relationship(back_populates="events", lazy="raise")

    __table_args__ = (
        Index("ix_case_events_case_id_timestamp", "case_id", "timestamp"),
        Index("ix_case_events_actor_timestamp", "actor", "timestamp"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<CaseEvent {self.id} {self.event_type} by={self.actor}>"


# ``CaseEvent``/``Case`` forward references are resolved at mapper
# configuration; the classes are defined in this module so no import cycle
# exists.
