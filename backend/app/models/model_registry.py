"""Registry of trained model artifacts and the dataset manifest they used.

Every assessment references the exact ``model_version`` it was scored with, so
a decision can be reproduced. ``feature_schema_version`` must match the live
feature contract or readiness fails (docs/architecture.md section 6).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    ID_LENGTH,
    MODEL_VERSION_ID_PREFIX,
    Base,
    new_id,
    utcnow,
)

if TYPE_CHECKING:
    from app.models.assessment import Assessment


class ModelVersion(Base):
    """A frozen, checksummed model artifact plus its evaluation provenance."""

    __tablename__ = "model_versions"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(MODEL_VERSION_ID_PREFIX),
    )
    #: SHA-256 (or similar) of the packaged artifact bundle. Unique so the
    #: same artifact cannot be registered twice.
    artifact_checksum: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )
    #: Manifest of the training data: generator version, seed, split sizes,
    #: class counts. JSON so it can evolve without a migration.
    dataset_manifest: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    #: Held-out evaluation metrics. Real measured numbers, never fabricated.
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    #: The feature contract version this artifact was trained against.
    feature_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="model",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_model_versions_trained_at", "trained_at"),
        Index("ix_model_versions_feature_schema_version", "feature_schema_version"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ModelVersion {self.id} schema={self.feature_schema_version}>"
