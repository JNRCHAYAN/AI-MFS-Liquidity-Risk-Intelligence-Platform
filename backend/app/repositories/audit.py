"""Repository for the append-only audit trail.

Audit events are written in the same transaction as the action they describe,
so a committed action always has its audit record. There is deliberately no
update or delete method: the trail is immutable from the application's side.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select

from app.models.audit import AuditEvent
from app.models.enums import AuditAction
from app.repositories.base import BaseRepository, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec


class AuditEventRepository(BaseRepository[AuditEvent]):
    """Writes and bounded reads for audit events."""

    model = AuditEvent

    SORTABLE: Mapping[str, Any] = {
        "timestamp": AuditEvent.timestamp,
        "id": AuditEvent.id,
    }

    def record(
        self,
        *,
        actor: str,
        action: AuditAction,
        object_type: str,
        object_id: str,
        request_id: str | None = None,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Append one audit event to the caller's transaction.

        Never pass secrets or raw request bodies in the state dictionaries.
        """
        event = AuditEvent(
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            request_id=request_id,
            before_state=before_state,
            after_state=after_state,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_for_object(
        self,
        object_type: str,
        object_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[AuditEvent]:
        """Audit history for one object, newest first, bounded."""
        return list(
            self.session.scalars(
                select(AuditEvent)
                .where(
                    AuditEvent.object_type == object_type,
                    AuditEvent.object_id == object_id,
                )
                .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        actor: str | None = None,
        action: AuditAction | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        request_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Page[AuditEvent]:
        """Paginated, filtered audit list."""
        stmt: Select[Any] = select(AuditEvent)
        if actor is not None:
            stmt = stmt.where(AuditEvent.actor == actor)
        if action is not None:
            stmt = stmt.where(AuditEvent.action == action)
        if object_type is not None:
            stmt = stmt.where(AuditEvent.object_type == object_type)
        if object_id is not None:
            stmt = stmt.where(AuditEvent.object_id == object_id)
        if request_id is not None:
            stmt = stmt.where(AuditEvent.request_id == request_id)
        if since is not None:
            stmt = stmt.where(
                AuditEvent.timestamp >= ensure_aware(since, name="since")
            )
        if until is not None:
            stmt = stmt.where(
                AuditEvent.timestamp < ensure_aware(until, name="until")
            )
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def count_for_request(self, request_id: str) -> int:
        """Number of audit events correlated with one request id."""
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(AuditEvent.request_id == request_id)
            )
            or 0
        )
