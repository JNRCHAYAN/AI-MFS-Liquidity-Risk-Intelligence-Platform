"""Persisted assessments and the evidence rows that justify them.

An assessment is the durable record of one causal scoring decision for one
transaction: the exact feature snapshot that was scored, the model and policy
versions in force, and the routing level. Evidence rows point back to it and
are what an analyst cites.

The feature snapshot is stored so a decision can be reproduced and audited
even after the feature contract evolves. It is a *snapshot*, not a live view.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    ASSESSMENT_ID_PREFIX,
    EVIDENCE_ID_PREFIX,
    ID_LENGTH,
    Base,
    new_id,
    utcnow,
)
from app.models.enums import EvidenceSource, PolicyLevel, pg_enum

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.model_registry import ModelVersion
    from app.models.transaction import Transaction


class Assessment(Base):
    """A persisted, reproducible scoring decision for one transaction.

    Deduplication: ``(transaction_id, model_version)`` is unique, so retrying
    a score for the same transaction with the same model is idempotent, while
    a deliberate re-score under a new model version creates a new row and
    preserves the old decision.
    """

    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(ASSESSMENT_ID_PREFIX),
    )
    transaction_id: Mapped[str] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    #: Ordered feature snapshot at scoring time. Keys are feature names from
    #: the frozen contract; values are the values actually passed to the model.
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    #: Feature contract version (app.core.config.FEATURE_SCHEMA_VERSION).
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    #: Raw classifier output. A score, not a probability, unless calibration
    #: has been validated. Nullable when the model was unavailable.
    raw_model_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Only populated when calibration was validated on reserved data.
    calibrated_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Isolation Forest result expressed as an empirical percentile over
    #: reference data. Explicitly NOT a probability of fraud.
    anomaly_percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    policy_level: Mapped[PolicyLevel] = mapped_column(
        pg_enum(PolicyLevel, name="policy_level"),
        nullable=False,
    )
    recommendation: Mapped[str] = mapped_column(String(64), nullable=False)
    #: Model artifact identifier, if a model was used.
    model_version: Mapped[str | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    #: Bounded, informational processing duration for observability.
    processing_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    transaction: Mapped[Transaction] = relationship(
        back_populates="assessment",
        lazy="raise",
    )
    #: Distinct from the ``model_version`` FK column: this is the ORM link to
    #: the registered artifact.
    model: Mapped[ModelVersion | None] = relationship(
        back_populates="assessments",
        lazy="raise",
    )
    evidence: Mapped[list[Evidence]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="Evidence.ordinal",
        lazy="raise",
    )
    alert: Mapped[Alert | None] = relationship(
        back_populates="assessment",
        uselist=False,
        lazy="raise",
    )

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "model_version",
            name="uq_assessments_transaction_id_model_version",
        ),
        Index("ix_assessments_transaction_id", "transaction_id"),
        Index(
            "ix_assessments_policy_level_assessed_at",
            "policy_level",
            "assessed_at",
        ),
        Index("ix_assessments_assessed_at", "assessed_at"),
        CheckConstraint(
            "calibrated_probability IS NULL OR "
            "(calibrated_probability >= 0 AND calibrated_probability <= 1)",
            name="calibrated_probability_range",
        ),
        CheckConstraint(
            "anomaly_percentile IS NULL OR "
            "(anomaly_percentile >= 0 AND anomaly_percentile <= 100)",
            name="anomaly_percentile_range",
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<Assessment {self.id} txn={self.transaction_id} "
            f"level={self.policy_level}>"
        )


class Evidence(Base):
    """One inspectable reason supporting an assessment.

    ``observed_value`` / ``baseline_value`` are stored as text so a value can
    carry its unit (e.g. ``"2.4x sender median"``) without the database
    pretending they are one common numeric unit. ``provenance`` records where
    the value came from (algorithm, dataset slice, window), so an analyst can
    trace a claim to its source.
    """

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(EVIDENCE_ID_PREFIX),
    )
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[EvidenceSource] = mapped_column(
        pg_enum(EvidenceSource, name="evidence_source"),
        nullable=False,
    )
    #: Stable reason code, e.g. "amount_ratio_high". Referenced by policy.
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    baseline_value: Mapped[str | None] = mapped_column(String(128), nullable=True)
    #: Analyst-facing explanation. Must be accurate and non-alarming.
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    #: The as-of time the observation is valid for. Equals the scored
    #: transaction's timestamp for causal evidence.
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provenance: Mapped[str | None] = mapped_column(String(255), nullable=True)
    #: Preserves display order and gives deterministic sort tie-breaking.
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    assessment: Mapped[Assessment] = relationship(
        back_populates="evidence",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_evidence_assessment_id_ordinal", "assessment_id", "ordinal"),
        Index("ix_evidence_source_code", "source", "code"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Evidence {self.id} code={self.code} source={self.source}>"
