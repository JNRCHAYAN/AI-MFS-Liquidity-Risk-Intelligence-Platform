"""Controlled vocabularies used across the schema.

Design choice (consistent throughout): enums are stored as **strings with a
CHECK constraint**, produced by :func:`pg_enum`. We deliberately do **not**
use native PostgreSQL ``ENUM`` types.

Rationale:

* A native type cannot be altered inside the same transaction that adds it,
  and adding a value later needs ``ALTER TYPE ... ADD VALUE``, which is not
  transactional on older PostgreSQL. String+CHECK stays trivially migratable.
* The allowed values appear verbatim in ``alembic upgrade --sql`` output, so
  the constraint is auditable offline without a live database.
* Membership is still enforced by the database, not only by Python.

Enum member *names* equal their *values* everywhere, so SQLAlchemy's default
of storing the member name is unambiguous.

Transaction types mirror ``app.intelligence.features.schema.TRANSACTION_TYPES``
but exclude the ``__unknown__`` fallback, which is an inference-time sentinel
and never a persisted transaction type.
"""

from __future__ import annotations

from enum import StrEnum

import sqlalchemy as sa


class EntityKind(StrEnum):
    """What a simulated ledger participant is."""

    CUSTOMER = "customer"
    AGENT = "agent"
    MERCHANT = "merchant"


class DeviceChannel(StrEnum):
    """Channel through which a device participated."""

    APP = "app"
    USSD = "ussd"
    AGENT_TERMINAL = "agent_terminal"
    WEB = "web"
    API = "api"


class TransactionType(StrEnum):
    """Ledger transaction type. Mirrors the frozen feature contract."""

    SEND_MONEY = "send_money"
    CASH_IN = "cash_in"
    CASH_OUT = "cash_out"
    MERCHANT_PAYMENT = "merchant_payment"
    BILL_PAYMENT = "bill_payment"
    MOBILE_RECHARGE = "mobile_recharge"
    AGENT_SETTLEMENT = "agent_settlement"


class TransactionStatus(StrEnum):
    """Simulated ledger resolution.

    NOTE: this is an **outcome** field. It is never available at scoring time
    and must never be read by the feature engine. It is listed in
    ``FORBIDDEN_INPUT_COLUMNS`` in the feature contract.
    """

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class PolicyLevel(StrEnum):
    """Deterministic policy routing level (see docs/architecture.md section 7)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    #: Missing data or an unavailable model. Reported explicitly, never
    #: silently treated as "low".
    INSUFFICIENT = "insufficient"


class RiskCategory(StrEnum):
    """Hypothesis attached to an alert.

    These are *hypotheses with evidence*, never a claim that fraud occurred.
    """

    ACCOUNT_TAKEOVER = "account_takeover"
    VELOCITY_BURST = "velocity_burst"
    MULE_NETWORK = "mule_network"
    CIRCULAR_FLOW = "circular_flow"
    AGENT_RISK = "agent_risk"
    SCAM_PATTERN = "scam_pattern"
    ANOMALY = "anomaly"
    MODEL_RISK = "model_risk"
    POLICY_REVIEW = "policy_review"


class EvidenceSource(StrEnum):
    """Which component produced an evidence row.

    Component outputs are kept separate and never averaged into a fake
    probability (docs/architecture.md section 7).
    """

    MODEL = "model"
    ANOMALY = "anomaly"
    GRAPH = "graph"
    AGENT = "agent"
    SCAM = "scam"
    POLICY = "policy"
    DEVICE = "device"
    LOCATION = "location"
    VELOCITY = "velocity"
    DATA_QUALITY = "data_quality"


class AlertSeverity(StrEnum):
    """Analyst-facing prioritisation band."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    """Lifecycle of an alert in the analyst queue."""

    OPEN = "open"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class CaseStatus(StrEnum):
    """Lifecycle of an investigation case."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    AWAITING_INFO = "awaiting_info"
    RESOLVED = "resolved"
    CLOSED = "closed"


class AnalystDisposition(StrEnum):
    """Analyst's recorded conclusion. Set only through the audited workflow."""

    PENDING = "pending"
    CONFIRMED_FRAUD = "confirmed_fraud"
    LIKELY_FRAUD = "likely_fraud"
    BENIGN = "benign"
    INCONCLUSIVE = "inconclusive"
    ESCALATED = "escalated"


class CaseEventType(StrEnum):
    """Append-only case timeline event kinds."""

    CREATED = "created"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    EVIDENCE_ATTACHED = "evidence_attached"
    EXPLANATION_GENERATED = "explanation_generated"
    ACTION_CONFIRMED = "action_confirmed"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class AuditAction(StrEnum):
    """Durable audit action kinds. Audit rows are append-only."""

    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    ACTION_CONFIRMED = "action_confirmed"
    EXPLANATION_GENERATED = "explanation_generated"
    SIMULATION_CREATED = "simulation_created"
    SIMULATION_STEPPED = "simulation_stepped"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_RESET = "simulation_reset"
    LOGIN = "login"
    EXPORT = "export"


class SimulationRunStatus(StrEnum):
    """Durable status of a synthetic simulation run."""

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


def pg_enum(enum_cls: type[StrEnum], *, name: str) -> sa.Enum:
    """Return a portable, CHECK-constrained column type for ``enum_cls``.

    ``native_enum=False`` compiles to ``VARCHAR`` plus a ``CHECK ... IN (...)``
    constraint named ``name`` (prefixed by the table via the metadata naming
    convention). ``create_constraint=True`` is required because SQLAlchemy 2.0
    defaults it to ``False``.

    ``values_callable`` makes the stored value the enum's *value* (lowercase,
    stable), not its Python member *name*. Without it SQLAlchemy would persist
    ``"SEND_MONEY"`` and the CHECK constraint would list member names, which
    would silently disagree with the feature contract's lowercase vocabulary.
    """
    values = [str(member.value) for member in enum_cls]
    return sa.Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda _enum, vals=values: vals,
        length=max(len(value) for value in values),
    )
