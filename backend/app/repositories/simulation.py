"""Repositories for simulation runs and the isolated scenario-truth table.

``ScenarioTruthRepository`` methods are all prefixed ``evaluation_`` to make it
obvious at every call site that they must never be used to build scoring
features. See the warning in ``app.models.simulation``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, delete, func, select
from sqlalchemy.exc import IntegrityError

from app.core.errors import ValidationFailed
from app.models.audit import AuditEvent
from app.models.enums import AuditAction, SimulationRunStatus
from app.models.simulation import ScenarioTruth, SimulationRun
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository, bounded_limit, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec


@dataclass(frozen=True)
class RunStatusCount:
    """Run counts for one status."""

    status: SimulationRunStatus
    count: int


@dataclass(frozen=True)
class RunResetResult:
    """Outcome of resetting one simulation run."""

    run: SimulationRun
    deleted_transactions: int


class SimulationRunRepository(BaseRepository[SimulationRun]):
    """Durable control state for reproducible synthetic runs.

    Runs are always scoped by id: resetting one run deletes only that run's
    transactions and leaves every other run and shared entity untouched.
    """

    model = SimulationRun

    SORTABLE: Mapping[str, Any] = {
        "created_at": SimulationRun.created_at,
        "id": SimulationRun.id,
        "status": SimulationRun.status,
    }

    def create(
        self,
        *,
        seed: int,
        scenario: str,
        simulated_clock: datetime,
        created_by: str,
        actor: str,
        request_id: str | None = None,
    ) -> SimulationRun:
        """Create a new run in the ``created`` state and audit it."""
        run = SimulationRun(
            seed=seed,
            scenario=scenario,
            simulated_clock=ensure_aware(simulated_clock, name="simulated_clock"),
            status=SimulationRunStatus.CREATED,
            created_by=created_by,
            events_emitted=0,
        )
        self.session.add(run)
        self.session.flush()
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.SIMULATION_CREATED,
                object_type="simulation_run",
                object_id=run.id,
                request_id=request_id,
                after_state={
                    "seed": seed,
                    "scenario": scenario,
                    "created_by": created_by,
                },
            )
        )
        self.session.flush()
        return run

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        status: SimulationRunStatus | None = None,
        created_by: str | None = None,
        scenario: str | None = None,
    ) -> Page[SimulationRun]:
        """Paginated, filtered run list."""
        stmt: Select[Any] = select(SimulationRun)
        if status is not None:
            stmt = stmt.where(SimulationRun.status == status)
        if created_by is not None:
            stmt = stmt.where(SimulationRun.created_by == created_by)
        if scenario is not None:
            stmt = stmt.where(SimulationRun.scenario == scenario)
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def set_status(
        self,
        run_id: str,
        status: SimulationRunStatus,
        *,
        actor: str,
        request_id: str | None = None,
    ) -> SimulationRun:
        """Change a run's status and audit it."""
        run = self.get_or_raise(run_id, label="Simulation run")
        before = run.status.value
        run.status = status
        audit_action = (
            AuditAction.SIMULATION_PAUSED
            if status is SimulationRunStatus.PAUSED
            else AuditAction.SIMULATION_STEPPED
        )
        self.session.add(
            AuditEvent(
                actor=actor,
                action=audit_action,
                object_type="simulation_run",
                object_id=run.id,
                request_id=request_id,
                before_state={"status": before},
                after_state={"status": status.value},
            )
        )
        self.session.flush()
        return run

    def advance(
        self,
        run_id: str,
        *,
        simulated_clock: datetime,
        actor: str,
        events_emitted_delta: int = 0,
        status: SimulationRunStatus | None = None,
        request_id: str | None = None,
    ) -> SimulationRun:
        """Advance a run's clock and progress counter.

        The simulated clock is monotonic non-decreasing: moving it backwards is
        rejected, because a replayed run must never generate events "before"
        work already done.
        """
        run = self.get_or_raise(run_id, label="Simulation run")
        new_clock = ensure_aware(simulated_clock, name="simulated_clock")
        if new_clock < run.simulated_clock:
            raise ValidationFailed(
                "simulated_clock must not move backwards.",
                details={
                    "current": run.simulated_clock.isoformat(),
                    "requested": new_clock.isoformat(),
                },
            )
        if events_emitted_delta < 0:
            raise ValidationFailed("events_emitted_delta must be >= 0.")

        before = {
            "simulated_clock": run.simulated_clock.isoformat(),
            "events_emitted": run.events_emitted,
            "status": run.status.value,
        }
        run.simulated_clock = new_clock
        run.events_emitted = run.events_emitted + events_emitted_delta
        run.last_step_at = new_clock
        if status is not None:
            run.status = status
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.SIMULATION_STEPPED,
                object_type="simulation_run",
                object_id=run.id,
                request_id=request_id,
                before_state=before,
                after_state={
                    "simulated_clock": run.simulated_clock.isoformat(),
                    "events_emitted": run.events_emitted,
                    "status": run.status.value,
                },
            )
        )
        self.session.flush()
        return run

    def reset(
        self,
        run_id: str,
        *,
        actor: str,
        request_id: str | None = None,
    ) -> RunResetResult:
        """Reset one run: delete its transactions and zero its progress.

        Scoped to ``run_id``. Shared entities, other runs and the audit trail
        are never touched. The database cascades to the run's assessments,
        evidence, alerts, cases and case events.
        """
        run = self.get_or_raise(run_id, label="Simulation run")
        deleted = self.session.execute(
            delete(Transaction).where(Transaction.scenario_run_id == run_id)
        ).rowcount
        run.events_emitted = 0
        run.status = SimulationRunStatus.CREATED
        run.simulated_clock = run.created_at
        run.last_step_at = None
        self.session.add(
            AuditEvent(
                actor=actor,
                action=AuditAction.SIMULATION_RESET,
                object_type="simulation_run",
                object_id=run.id,
                request_id=request_id,
                after_state={
                    "deleted_transactions": int(deleted or 0),
                    "events_emitted": 0,
                },
            )
        )
        self.session.flush()
        return RunResetResult(run=run, deleted_transactions=int(deleted or 0))

    def count_by_status(self) -> list[RunStatusCount]:
        """Run counts grouped by status (database aggregate)."""
        rows = self.session.execute(
            select(SimulationRun.status, func.count()).group_by(SimulationRun.status)
        ).all()
        return [RunStatusCount(status=row[0], count=int(row[1])) for row in rows]


@dataclass(frozen=True)
class EvaluationTruthCounts:
    """Ground-truth label counts for one run (evaluation view only)."""

    total: int
    fraud: int
    benign: int


class ScenarioTruthRepository(BaseRepository[ScenarioTruth]):
    """Ground-truth access for OFFLINE EVALUATION ONLY.

    Every method is prefixed ``evaluation_``. This repository must never be
    imported by the feature engine, the policy layer or the scoring service.
    Its results must never appear in a scoring response.
    """

    model = ScenarioTruth

    def evaluation_upsert_many(self, items: Sequence[ScenarioTruth]) -> int:
        """Insert ground-truth rows, skipping duplicates on transaction id."""
        if not items:
            return 0
        inserted = 0
        for item in items:
            existing = self.evaluation_get_for_transaction(item.transaction_id) if item.transaction_id else None
            if existing is not None:
                continue
            try:
                with self.session.begin_nested():
                    self.session.add(item)
            except IntegrityError:
                continue
            inserted += 1
        self.session.flush()
        return inserted

    def evaluation_get_for_transaction(
        self,
        transaction_id: str,
    ) -> ScenarioTruth | None:
        """Ground-truth label for a transaction, if one exists."""
        return self.session.scalars(
            select(ScenarioTruth)
            .where(ScenarioTruth.transaction_id == transaction_id)
            .limit(1)
        ).first()

    def evaluation_list_for_run(
        self,
        scenario_run_id: str,
        *,
        limit: int = 500,
        offset: int = 0,
    ) -> Sequence[ScenarioTruth]:
        """Bounded ground-truth list for a run, ordered by transaction id."""
        bounded = bounded_limit(limit, default=500, maximum=2000)
        return list(
            self.session.scalars(
                select(ScenarioTruth)
                .where(ScenarioTruth.scenario_run_id == scenario_run_id)
                .order_by(ScenarioTruth.transaction_id.asc().nulls_last(), ScenarioTruth.id.asc())
                .limit(bounded)
                .offset(offset)
            ).all()
        )

    def evaluation_counts_for_run(self, scenario_run_id: str) -> EvaluationTruthCounts:
        """Fraud/benign totals for a run (database aggregate)."""
        row = self.session.execute(
            select(
                func.count(),
                func.count().filter(ScenarioTruth.is_fraud.is_(True)),
            ).where(ScenarioTruth.scenario_run_id == scenario_run_id)
        ).one()
        total = int(row[0] or 0)
        fraud = int(row[1] or 0)
        return EvaluationTruthCounts(total=total, fraud=fraud, benign=total - fraud)
