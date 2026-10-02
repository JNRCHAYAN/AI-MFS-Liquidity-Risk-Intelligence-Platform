"""Canonical feature contract for upay Shield.

SINGLE SOURCE OF TRUTH. Both training (`ml/`) and online inference
(`backend/app/intelligence/`) import this module. There must never be a second
copy of these definitions.

Design rules enforced by this module (see AGENTS.md and docs/architecture.md):

* Every feature is computed from events **strictly preceding** the scored
  transaction. Nothing here may read the current transaction's final
  resolution, any future event, a fraud label, or a later analyst decision.
* Money is integer **poisha**. Never a float.
* Behavioural hour/day are derived in Asia/Dhaka, consistently in both paths.
* Every feature declares a missing-value strategy. Cold-start entities get an
  explicit `insufficient_history` flag rather than an invented personal
  baseline.
* Categories are encoded through a **persisted mapping**; unseen categories
  must resolve to a stable fallback, never a crash and never an index that
  happens to be free.

Bump `FEATURE_SCHEMA_VERSION` on any change to names, order, dtype or
semantics. Model artifacts record the version they were trained against; a
mismatch must fail readiness rather than silently score with wrong inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Bump on ANY change to the feature set, its order, dtype or semantics.
FEATURE_SCHEMA_VERSION = "1.0.0"


class DType(str, Enum):
    """Storage dtype of a feature value."""

    INT = "int64"
    FLOAT = "float64"
    BOOL = "bool"
    CATEGORY = "category"


class MissingStrategy(str, Enum):
    """How a feature's absent value is represented.

    Declaring this explicitly prevents the classic silent bug where a missing
    history is encoded as a legitimate zero and the model reads "no history"
    as "historically zero activity".
    """

    # Genuine zero is meaningful (e.g. no transactions in the last 5 minutes).
    ZERO = "zero"
    # Absent because the entity has too little history; must set the
    # insufficient_history flag and use the documented cohort baseline.
    COHORT_BASELINE = "cohort_baseline"
    # Absent is semantically distinct from any number.
    SENTINEL_NULL = "sentinel_null"
    # Only ever set by its own detector flag.
    FLAG_DEPENDENT = "flag_dependent"


class FeatureGroup(str, Enum):
    """Logical grouping, used for evidence presentation and slicing."""

    AMOUNT = "amount"
    TEMPORAL = "temporal"
    VELOCITY = "velocity"
    NOVELTY = "novelty"
    DEVICE = "device"
    LOCATION = "location"
    COUNTERPARTY = "counterparty"
    FLOW = "flow"
    AGENT = "agent"
    QUALITY = "quality"


@dataclass(frozen=True)
class FeatureSpec:
    """Declarative specification of one feature.

    Attributes:
        name: Stable column name. Renaming is a schema-version bump.
        dtype: Storage dtype.
        group: Logical group for evidence and slicing.
        unit: Human-readable unit, shown in evidence text. Empty for pure
            counters and flags. Never invent a unit.
        window: Computation window, or None for point-in-time features.
        missing: Strategy applied when the value cannot be computed.
        description: One line explaining what the feature means. This text is
            surfaced to analysts, so it must be accurate and non-alarming.
        min_history: Minimum number of prior events required before this
            feature is considered trustworthy. Below this, `missing` applies.
    """

    name: str
    dtype: DType
    group: FeatureGroup
    unit: str
    window: str | None
    missing: MissingStrategy
    description: str
    min_history: int = 0

    def __post_init__(self) -> None:
        if not self.name.islower() or " " in self.name:
            raise ValueError(
                f"Feature name must be lower_snake_case, got {self.name!r}"
            )


# ---------------------------------------------------------------------------
# Category vocabularies
#
# Persisted mappings. `__unknown__` is the mandatory stable fallback for any
# category value not seen during training. Order is significant and frozen;
# appending is a minor version bump, reordering or removing is a major one.
# ---------------------------------------------------------------------------

TRANSACTION_TYPES: tuple[str, ...] = (
    "__unknown__",
    "send_money",
    "cash_in",
    "cash_out",
    "merchant_payment",
    "bill_payment",
    "mobile_recharge",
    "agent_settlement",
)

CHANNELS: tuple[str, ...] = (
    "__unknown__",
    "app",
    "ussd",
    "agent_terminal",
    "web",
    "api",
)

UNKNOWN_CATEGORY = "__unknown__"


# ---------------------------------------------------------------------------
# The feature set. ORDER IS PART OF THE CONTRACT: model artifacts store the
# ordered feature list, and inference must build the vector in this order.
# ---------------------------------------------------------------------------

FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    # --- Amount ------------------------------------------------------------
    FeatureSpec(
        name="amount_poisha",
        dtype=DType.INT,
        group=FeatureGroup.AMOUNT,
        unit="poisha",
        window=None,
        missing=MissingStrategy.SENTINEL_NULL,
        description="Transaction amount in integer poisha.",
    ),
    FeatureSpec(
        name="amount_bdt",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="BDT",
        window=None,
        missing=MissingStrategy.SENTINEL_NULL,
        description="Transaction amount in BDT for display and coarse thresholds.",
    ),
    FeatureSpec(
        name="sender_prior_mean_amount_30d",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="poisha",
        window="30d",
        missing=MissingStrategy.COHORT_BASELINE,
        description="Mean amount the sender paid in the 30 days before this transaction.",
        min_history=3,
    ),
    FeatureSpec(
        name="sender_prior_median_amount_30d",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="poisha",
        window="30d",
        missing=MissingStrategy.COHORT_BASELINE,
        description="Median amount the sender paid in the 30 days before this transaction.",
        min_history=3,
    ),
    FeatureSpec(
        name="sender_prior_std_amount_30d",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="poisha",
        window="30d",
        missing=MissingStrategy.COHORT_BASELINE,
        description="Standard deviation of the sender's prior 30-day amounts.",
        min_history=3,
    ),
    FeatureSpec(
        name="amount_ratio_to_sender_median",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="ratio",
        window="30d",
        missing=MissingStrategy.COHORT_BASELINE,
        description="This amount divided by the sender's prior median amount.",
        min_history=3,
    ),
    FeatureSpec(
        name="amount_robust_deviation",
        dtype=DType.FLOAT,
        group=FeatureGroup.AMOUNT,
        unit="MAD-scaled score",
        window="30d",
        missing=MissingStrategy.COHORT_BASELINE,
        description=(
            "Robust deviation of this amount from the sender's history, scaled "
            "by median absolute deviation. Preferred over standard deviation "
            "because it is not distorted by the sender's own past outliers."
        ),
        min_history=5,
    ),
    # --- Temporal ----------------------------------------------------------
    FeatureSpec(
        name="local_hour",
        dtype=DType.INT,
        group=FeatureGroup.TEMPORAL,
        unit="hour",
        window=None,
        missing=MissingStrategy.SENTINEL_NULL,
        description="Hour of day in Asia/Dhaka, 0-23.",
    ),
    FeatureSpec(
        name="local_day_of_week",
        dtype=DType.INT,
        group=FeatureGroup.TEMPORAL,
        unit="day index",
        window=None,
        missing=MissingStrategy.SENTINEL_NULL,
        description="Day of week in Asia/Dhaka, Monday=0.",
    ),
    FeatureSpec(
        name="seconds_since_prev_txn",
        dtype=DType.FLOAT,
        group=FeatureGroup.TEMPORAL,
        unit="seconds",
        window=None,
        missing=MissingStrategy.COHORT_BASELINE,
        description="Seconds since the sender's previous outgoing transaction.",
        min_history=1,
    ),
    FeatureSpec(
        name="seconds_since_prev_login",
        dtype=DType.FLOAT,
        group=FeatureGroup.TEMPORAL,
        unit="seconds",
        window=None,
        missing=MissingStrategy.COHORT_BASELINE,
        description="Seconds since the sender's previous login event.",
        min_history=1,
    ),
    # --- Velocity ----------------------------------------------------------
    FeatureSpec(
        name="txn_count_prev_5m",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="count",
        window="5m",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing transaction count in the preceding 5 minutes.",
    ),
    FeatureSpec(
        name="txn_count_prev_10m",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="count",
        window="10m",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing transaction count in the preceding 10 minutes.",
    ),
    FeatureSpec(
        name="txn_count_prev_1h",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="count",
        window="1h",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing transaction count in the preceding hour.",
    ),
    FeatureSpec(
        name="txn_count_prev_24h",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="count",
        window="24h",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing transaction count in the preceding 24 hours.",
    ),
    FeatureSpec(
        name="amount_sum_prev_5m",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="poisha",
        window="5m",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing amount sum in the preceding 5 minutes.",
    ),
    FeatureSpec(
        name="amount_sum_prev_1h",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="poisha",
        window="1h",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing amount sum in the preceding hour.",
    ),
    FeatureSpec(
        name="amount_sum_prev_24h",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="poisha",
        window="24h",
        missing=MissingStrategy.ZERO,
        description="Sender's outgoing amount sum in the preceding 24 hours.",
    ),
    FeatureSpec(
        name="distinct_recipients_prev_1h",
        dtype=DType.INT,
        group=FeatureGroup.VELOCITY,
        unit="count",
        window="1h",
        missing=MissingStrategy.ZERO,
        description="Distinct recipients the sender paid in the preceding hour.",
    ),
    # --- Novelty -----------------------------------------------------------
    FeatureSpec(
        name="recipient_is_new",
        dtype=DType.BOOL,
        group=FeatureGroup.NOVELTY,
        unit="",
        window="all-history",
        missing=MissingStrategy.ZERO,
        description="Whether the sender has never previously paid this recipient.",
    ),
    FeatureSpec(
        name="recipient_account_age_days",
        dtype=DType.FLOAT,
        group=FeatureGroup.NOVELTY,
        unit="days",
        window=None,
        missing=MissingStrategy.COHORT_BASELINE,
        description="Age in days of the recipient account at scoring time.",
    ),
    FeatureSpec(
        name="recipient_distinct_senders_prior",
        dtype=DType.INT,
        group=FeatureGroup.COUNTERPARTY,
        unit="count",
        window="all-history",
        missing=MissingStrategy.ZERO,
        description=(
            "Distinct senders who paid this recipient before this transaction. "
            "A high value is context, not evidence of wrongdoing: legitimate "
            "merchants and agents have many senders."
        ),
    ),
    # --- Device ------------------------------------------------------------
    FeatureSpec(
        name="device_is_new",
        dtype=DType.BOOL,
        group=FeatureGroup.DEVICE,
        unit="",
        window="all-history",
        missing=MissingStrategy.ZERO,
        description="Whether this device has never been seen for this entity before.",
    ),
    FeatureSpec(
        name="device_age_hours",
        dtype=DType.FLOAT,
        group=FeatureGroup.DEVICE,
        unit="hours",
        window=None,
        missing=MissingStrategy.FLAG_DEPENDENT,
        description="Hours since this device was first seen for this entity.",
    ),
    FeatureSpec(
        name="failed_logins_prev_1h",
        dtype=DType.INT,
        group=FeatureGroup.DEVICE,
        unit="count",
        window="1h",
        missing=MissingStrategy.ZERO,
        description=(
            "Failed login attempts for this entity in the preceding hour. "
            "Corroborating context only: failed logins alone do not establish "
            "account takeover."
        ),
    ),
    # --- Location ----------------------------------------------------------
    FeatureSpec(
        name="location_distance_km",
        dtype=DType.FLOAT,
        group=FeatureGroup.LOCATION,
        unit="km",
        window="30d",
        missing=MissingStrategy.FLAG_DEPENDENT,
        description=(
            "Distance in km from the entity's recent synthetic activity centroid. "
            "Meaningful only alongside location_missing and travel time."
        ),
    ),
    FeatureSpec(
        name="location_missing",
        dtype=DType.BOOL,
        group=FeatureGroup.LOCATION,
        unit="",
        window=None,
        missing=MissingStrategy.ZERO,
        description="Whether location could not be resolved for this transaction.",
    ),
    FeatureSpec(
        name="location_travel_plausible",
        dtype=DType.BOOL,
        group=FeatureGroup.LOCATION,
        unit="",
        window=None,
        missing=MissingStrategy.FLAG_DEPENDENT,
        description=(
            "Whether the elapsed time since the previous location makes the "
            "observed movement physically plausible. Prevents flagging benign "
            "travel as an impossible-velocity event."
        ),
    ),
    # --- Flow --------------------------------------------------------------
    FeatureSpec(
        name="pass_through_ratio_prev_1h",
        dtype=DType.FLOAT,
        group=FeatureGroup.FLOW,
        unit="ratio",
        window="1h",
        missing=MissingStrategy.COHORT_BASELINE,
        description=(
            "Share of the sender's incoming value that left again within the "
            "preceding hour. High values are consistent with pass-through "
            "behaviour but also with ordinary agent settlement."
        ),
    ),
    FeatureSpec(
        name="sender_prior_incoming_count",
        dtype=DType.INT,
        group=FeatureGroup.FLOW,
        unit="count",
        window="all-history",
        missing=MissingStrategy.ZERO,
        description="Lifetime count of incoming transactions to this sender.",
    ),
    FeatureSpec(
        name="sender_prior_outgoing_count",
        dtype=DType.INT,
        group=FeatureGroup.FLOW,
        unit="count",
        window="all-history",
        missing=MissingStrategy.ZERO,
        description="Lifetime count of outgoing transactions from this sender.",
    ),
    # --- Agent -------------------------------------------------------------
    FeatureSpec(
        name="agent_cash_out_deviation",
        dtype=DType.FLOAT,
        group=FeatureGroup.AGENT,
        unit="MAD-scaled score",
        window="7d",
        missing=MissingStrategy.COHORT_BASELINE,
        description=(
            "Deviation of the counterparty agent's recent cash-out volume from "
            "its own prior median, scaled by MAD."
        ),
        min_history=10,
    ),
    FeatureSpec(
        name="agent_peer_deviation",
        dtype=DType.FLOAT,
        group=FeatureGroup.AGENT,
        unit="MAD-scaled score",
        window="7d",
        missing=MissingStrategy.COHORT_BASELINE,
        description=(
            "Deviation of the counterparty agent from its peer group (region, "
            "activity band, agent age), scaled by the peer MAD."
        ),
        min_history=10,
    ),
    # --- Quality -----------------------------------------------------------
    FeatureSpec(
        name="insufficient_history",
        dtype=DType.BOOL,
        group=FeatureGroup.QUALITY,
        unit="",
        window=None,
        missing=MissingStrategy.ZERO,
        description=(
            "Set when the sender has too little history for personal baselines "
            "to be trusted. When set, cohort baselines were used and the "
            "assessment must be presented with reduced confidence."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Derived collections used by both training and inference.
# ---------------------------------------------------------------------------

FEATURE_NAMES: tuple[str, ...] = tuple(spec.name for spec in FEATURE_SPECS)

#: Ordered model input vector definition.
FEATURE_VECTOR: tuple[str, ...] = FEATURE_NAMES

#: Names that must never be treated as model input, even if present in a
#: dataframe. Guards against label leakage in the training pipeline.
FORBIDDEN_INPUT_COLUMNS: frozenset[str] = frozenset(
    {
        # Synthetic ground truth from the simulator.
        "is_fraud",
        "fraud_label",
        "scenario_truth",
        "scenario_truth_label",
        "ground_truth",
        # Resolution / outcome fields, unknown at scoring time.
        "status",
        "final_status",
        "resolved_at",
        # Analyst outcomes, strictly later than the decision.
        "analyst_disposition",
        "resolution_note",
        "case_status",
    }
)

_SPEC_BY_NAME: dict[str, FeatureSpec] = {spec.name: spec for spec in FEATURE_SPECS}


def get_spec(name: str) -> FeatureSpec:
    """Return the spec for a feature name.

    Raises:
        KeyError: if the name is not part of the frozen contract. Callers must
            not silently ignore unknown features.
    """
    try:
        return _SPEC_BY_NAME[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(
            f"Unknown feature {name!r}. The feature contract is frozen at "
            f"version {FEATURE_SCHEMA_VERSION}; adding a feature requires a "
            f"version bump in backend/app/intelligence/features/schema.py."
        ) from exc


def group_of(name: str) -> FeatureGroup:
    """Return the logical group a feature belongs to."""
    return get_spec(name).group


def cohort_baseline_features() -> tuple[str, ...]:
    """Features that require a documented cohort fallback for cold start."""
    return tuple(
        spec.name
        for spec in FEATURE_SPECS
        if spec.missing is MissingStrategy.COHORT_BASELINE
    )


def assert_no_forbidden_columns(columns: list[str] | tuple[str, ...]) -> None:
    """Fail loudly if any label or outcome column is about to be used as input.

    This is the single guard that keeps synthetic ground truth and post-hoc
    outcomes out of the model's inputs. It is called by the training pipeline
    and by tests.
    """
    leaked = sorted(set(columns) & FORBIDDEN_INPUT_COLUMNS)
    if leaked:
        raise ValueError(
            "Label/outcome columns must never be used as model input. "
            f"Found: {leaked}. See FORBIDDEN_INPUT_COLUMNS in "
            "backend/app/intelligence/features/schema.py."
        )
