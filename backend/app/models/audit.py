"""Durable, append-only audit trail.

Every privileged mutation records who did what to which object, correlated by
request ID, with before/after state. Audit rows are never deleted by the
application and carry no foreign key to the objects they describe, so they
survive even when a simulation run is reset.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AUDIT_ID_PREFIX, ID_LENGTH, Base, new_id, utcnow
from app.models.enums import AuditAction, pg_enum


class AuditEvent(Base):
    """One recorded action. Append-only: the repository exposes no update/delete."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(AUDIT_ID_PREFIX),
    )
    #: Who performed the action (analyst user id, or "system").
    actor: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    action: Mapped[AuditAction] = mapped_column(
        pg_enum(AuditAction, name="audit_action"),
        nullable=False,
    )
    #: Type of the affected object (e.g. "case", "alert", "simulation_run").
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Identifier of the affected object. Not a foreign key by design.
    object_id: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    #: Correlates the audit row with the HTTP request that caused it.
    request_id: Mapped[str | None] = mapped_column(String(ID_LENGTH), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    #: State before the action, for reversible diagnosis. Secrets are never
    #: written here; repositories store only the changed business fields.
    before_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    #: State after the action.
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_audit_events_object", "object_type", "object_id", "timestamp"),
        Index("ix_audit_events_actor_timestamp", "actor", "timestamp"),
        Index("ix_audit_events_request_id", "request_id"),
        Index("ix_audit_events_timestamp", "timestamp"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<AuditEvent {self.id} {self.actor} {self.action} "
            f"{self.object_type}:{self.object_id}>"
        )
