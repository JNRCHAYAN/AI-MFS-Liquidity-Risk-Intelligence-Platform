"""Repositories for ledger participants, devices and login history."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError

from app.models.entity import Device, Entity, LoginEvent
from app.models.enums import EntityKind
from app.repositories.base import BaseRepository, UpsertResult, bounded_limit, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec


@dataclass(frozen=True)
class KindCount:
    """Row count for one entity kind."""

    kind: EntityKind
    count: int


class EntityRepository(BaseRepository[Entity]):
    """CRUD and bounded listing for simulated entities."""

    model = Entity

    SORTABLE: Mapping[str, Any] = {
        "created_at": Entity.created_at,
        "entity_id": Entity.entity_id,
        "kind": Entity.kind,
        "region": Entity.region,
    }

    def upsert(self, entity: Entity) -> UpsertResult[Entity]:
        """Insert ``entity`` unless its id already exists (idempotent replay)."""
        existing = self.get(entity.entity_id)
        if existing is not None:
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(entity)
        except IntegrityError:
            existing = self.get(entity.entity_id)
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(entity, True)

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        kind: EntityKind | None = None,
        region: str | None = None,
        peer_group: str | None = None,
    ) -> Page[Entity]:
        """Paginated, filtered entity list with a stable total order."""
        stmt: Select[Any] = select(Entity)
        if kind is not None:
            stmt = stmt.where(Entity.kind == kind)
        if region is not None:
            stmt = stmt.where(Entity.region == region)
        if peer_group is not None:
            stmt = stmt.where(Entity.peer_group == peer_group)
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def list_by_ids(self, entity_ids: Sequence[str]) -> Sequence[Entity]:
        """Fetch a bounded set of entities by id (for batch evidence lookup)."""
        if not entity_ids:
            return []
        bounded = list(dict.fromkeys(entity_ids))[:500]
        return list(self.session.scalars(select(Entity).where(Entity.entity_id.in_(bounded))).all())

    def count_by_kind(self) -> list[KindCount]:
        """Aggregate entity counts by kind in the database, not in Python."""
        rows = self.session.execute(
            select(Entity.kind, func.count()).group_by(Entity.kind)
        ).all()
        return [KindCount(kind=row[0], count=int(row[1])) for row in rows]


class DeviceRepository(BaseRepository[Device]):
    """CRUD for simulated device fingerprints."""

    model = Device

    SORTABLE: Mapping[str, Any] = {
        "first_seen_at": Device.first_seen_at,
        "device_id": Device.device_id,
    }

    def upsert(self, device: Device) -> UpsertResult[Device]:
        """Insert ``device`` unless its id already exists."""
        existing = self.get(device.device_id)
        if existing is not None:
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(device)
        except IntegrityError:
            existing = self.get(device.device_id)
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(device, True)

    def list_for_entity(self, entity_id: str, *, limit: int = 50) -> Sequence[Device]:
        """Bounded device list for one entity, newest first (stable order)."""
        bounded = bounded_limit(limit, default=50, maximum=500)
        return list(
            self.session.scalars(
                select(Device)
                .where(Device.entity_id == entity_id)
                .order_by(Device.first_seen_at.desc(), Device.device_id.asc())
                .limit(bounded)
            ).all()
        )

    def first_seen_at(self, device_id: str, entity_id: str) -> datetime | None:
        """Return when this device was first seen for this entity, if known.

        One bounded single-row query; used by the device-novelty feature.
        """
        return self.session.scalar(
            select(Device.first_seen_at)
            .where(Device.device_id == device_id, Device.entity_id == entity_id)
            .limit(1)
        )


class LoginEventRepository(BaseRepository[LoginEvent]):
    """Writes and causal reads for login events."""

    model = LoginEvent

    SORTABLE: Mapping[str, Any] = {
        "timestamp": LoginEvent.timestamp,
        "id": LoginEvent.id,
    }

    def upsert(self, event: LoginEvent) -> UpsertResult[LoginEvent]:
        """Insert ``event`` unless its id already exists."""
        existing = self.get(event.id)
        if existing is not None:
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(event)
        except IntegrityError:
            existing = self.get(event.id)
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(event, True)

    def events_before(
        self,
        entity_id: str,
        as_of: datetime,
        *,
        success: bool | None = None,
        order_desc: bool = True,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[LoginEvent]:
        """Return this entity's login events **strictly before** ``as_of``.

        Causality guarantee: the predicate is ``timestamp < as_of`` (never
        ``<=``), so an event at exactly ``as_of`` is excluded. Ties on equal
        timestamps are broken by ``id``, so the order is deterministic and
        train/inference parity holds. ``as_of`` must be timezone-aware.
        """
        moment = ensure_aware(as_of, name="as_of")
        bounded = bounded_limit(limit, default=200, maximum=1000)
        order = (
            (LoginEvent.timestamp.desc(), LoginEvent.id.desc())
            if order_desc
            else (LoginEvent.timestamp.asc(), LoginEvent.id.asc())
        )
        stmt = select(LoginEvent).where(
            LoginEvent.entity_id == entity_id,
            LoginEvent.timestamp < moment,
        )
        if success is not None:
            stmt = stmt.where(LoginEvent.success == success)
        return list(self.session.scalars(stmt.order_by(*order).limit(bounded).offset(offset)).all())

    def count_failed_before(
        self,
        entity_id: str,
        *,
        start: datetime,
        as_of: datetime,
    ) -> int:
        """Count failed logins in ``[start, as_of)`` as a database aggregate.

        Used for the ``failed_logins_prev_1h`` feature without loading rows.
        """
        lower = ensure_aware(start, name="start")
        upper = ensure_aware(as_of, name="as_of")
        total = self.session.scalar(
            select(func.count())
            .select_from(LoginEvent)
            .where(
                LoginEvent.entity_id == entity_id,
                LoginEvent.timestamp >= lower,
                LoginEvent.timestamp < upper,
                LoginEvent.success.is_(False),
            )
        )
        return int(total or 0)
