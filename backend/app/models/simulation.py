"""Synthetic simulation runs and the isolated ground-truth table.

Two distinct concerns live here:

* :class:`SimulationRun` — durable state of a reproducible synthetic run
  (seed, scenario, simulated clock, progress). Controls are scoped by run ID;
  resetting a run never wipes unrelated records.
* :class:`ScenarioTruth` — the synthetic ground truth produced by the
  generator.

.. warning::

   ``scenario_truth`` MUST NEVER be joined into, or otherwise read by, any
   scoring feature calculation. It exists only for offline evaluation and for
   the restricted "show scenario truth" demo view. It is deliberately a
   separate table with no relationship to ``assessments`` or ``transactions``
   so that an accidental feature join is structurally awkward. Access is
   exposed only through ``ScenarioTruthRepository.evaluation_*`` methods, and
   the feature contract lists ``scenario_truth`` in ``FORBIDDEN_INPUT_COLUMNS``.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    ID_LENGTH,
    SCENARIO_TRUTH_ID_PREFIX,
    SIMULATION_RUN_ID_PREFIX,
    Base,
    TimestampMixin,
    new_id,
    utcnow,
)
from app.models.enums import SimulationRunStatus, pg_enum

if TYPE_CHECKING:
    from app.models.transaction import Transaction


class SimulationRun(TimestampMixin, Base):
    """Durable, reproducible state for one synthetic simulation run."""

    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(SIMULATION_RUN_ID_PREFIX),
    )
    #: Deterministic RNG seed. Reproducing a run requires the same seed.
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    #: Scenario key, e.g. "ato" or "benign_travel".
    scenario: Mapped[str] = mapped_column(String(64), nullable=False)
    #: The simulated "now". Events are generated at or before this clock.
    simulated_clock: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    status: Mapped[SimulationRunStatus] = mapped_column(
        pg_enum(SimulationRunStatus, name="simulation_run_status"),
        nullable=False,
        default=SimulationRunStatus.CREATED,
    )
    #: Analyst/admin identity that created the run.
    created_by: Mapped[str] = mapped_column(String(ID_LENGTH), nullable=False)
    #: Number of transactions emitted so far, for bounded progress reporting.
    events_emitted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_step_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    transactions: Mapped[list[Transaction]] = relationship(
        back_populates="scenario_run",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_simulation_runs_status_created_at", "status", "created_at"),
        Index("ix_simulation_runs_created_by_created_at", "created_by", "created_at"),
        Index("ix_simulation_runs_scenario", "scenario"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<SimulationRun {self.id} scenario={self.scenario} {self.status}>"


class ScenarioTruth(Base):
    """Synthetic ground truth. OFFLINE EVALUATION ONLY — never a feature input.

    See the module docstring warning. There is intentionally no ORM
    relationship from this class to transactions or assessments.
    """

    __tablename__ = "scenario_truth"

    id: Mapped[str] = mapped_column(
        String(ID_LENGTH),
        primary_key=True,
        default=lambda: new_id(SCENARIO_TRUTH_ID_PREFIX),
    )
    scenario_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    #: The transaction this label applies to, when the label is per-event.
    transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=True,
    )
    #: The entity this label applies to, when the label is per-account.
    entity_id: Mapped[str | None] = mapped_column(
        ForeignKey("entities.entity_id", ondelete="CASCADE"),
        nullable=True,
    )
    scenario: Mapped[str] = mapped_column(String(64), nullable=False)
    is_fraud: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: Fraud family label for slice reporting, e.g. "mule_fan_in".
    fraud_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_scenario_truth_transaction_id"),
        Index("ix_scenario_truth_run_scenario", "scenario_run_id", "scenario"),
        Index("ix_scenario_truth_is_fraud_family", "is_fraud", "fraud_family"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<ScenarioTruth {self.id} txn={self.transaction_id} "
            f"fraud={self.is_fraud} family={self.fraud_family}>"
        )
