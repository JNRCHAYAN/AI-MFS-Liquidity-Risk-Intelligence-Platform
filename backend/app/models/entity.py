"""Ledger participants, their devices and their login history.

Simulated synthetic entities only — never real account holders.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    DEVICE_ID_PREFIX,
    ENTITY_ID_PREFIX,
    ID_LENGTH,
    Base,
    TimestampMixin,
    new_id,
    utcnow,
)
from app.models.enums import DeviceChannel, EntityKind, pg_enum

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class Entity(TimestampMixin, Base):
    """A simulated wallet, merchant or agent.

    ``peer_group`` is the comparison cohort used by the agent risk module
    (region + activity band + agent age). It is intentionally a free-form
    label; the module documents the denominator it uses.
    """

    __tablename__ = "entities"

    entity_id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(ENTITY_ID_PREFIX),
    )
    kind: Mapped[EntityKind] = mapped_column(
        pg_enum(EntityKind, name="entity_kind"),
        nullable=False,
        index=True,
    )
    #: Synthetic region label, e.g. "dhaka". Not a real address.
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    #: Comparison cohort for peer-group deviations.
    peer_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # ``created_at`` (from TimestampMixin) doubles as the synthetic account
    # age start used by the "recipient account age" feature.

    devices: Mapped[list[Device]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    login_events: Mapped[list[LoginEvent]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
        lazy="raise",
    )
    # Two FK paths to the same table need explicit foreign_keys on both sides.
    sent_transactions: Mapped[list[Transaction]] = relationship(
        foreign_keys="Transaction.sender_id",
        back_populates="sender",
        lazy="raise",
    )
    received_transactions: Mapped[list[Transaction]] = relationship(
        foreign_keys="Transaction.receiver_id",
        back_populates="receiver",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_entities_kind_region", "kind", "region"),
        Index("ix_entities_peer_group", "peer_group"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Entity {self.entity_id} kind={self.kind}>"


class Device(Base):
    """A simulated device fingerprint belonging to one entity.

    ``first_seen_at`` anchors the "device novelty" and "device age" features.
    """

    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(DEVICE_ID_PREFIX),
    )
    entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    channel: Mapped[DeviceChannel] = mapped_column(
        pg_enum(DeviceChannel, name="device_channel"),
        nullable=False,
    )

    entity: Mapped[Entity] = relationship(back_populates="devices", lazy="raise")

    __table_args__ = (
        Index("ix_devices_entity_channel", "entity_id", "channel"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Device {self.device_id} entity={self.entity_id}>"


class LoginEvent(Base):
    """An authentication attempt used as corroborating ATO evidence.

    Failed logins alone never establish account takeover; the pattern is
    context for other evidence (docs/architecture.md section 6).
    """

    __tablename__ = "login_events"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id("lgn"),
    )
    entity_id: Mapped[str] = mapped_column(
        ForeignKey("entities.entity_id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    device_id: Mapped[str | None] = mapped_column(
        ForeignKey("devices.device_id", ondelete="SET NULL"),
        nullable=True,
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    #: Synthetic location label. Never a real coordinate set.
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)

    entity: Mapped[Entity] = relationship(back_populates="login_events", lazy="raise")

    __table_args__ = (
        # The mandatory entity/time access path for "failed logins in the
        # preceding hour" and "seconds since previous login".
        Index("ix_login_events_entity_timestamp", "entity_id", "timestamp"),
        Index("ix_login_events_timestamp", "timestamp"),
        CheckConstraint("success IN (true, false)", name="login_success_bool"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<LoginEvent {self.id} entity={self.entity_id} ok={self.success}>"
