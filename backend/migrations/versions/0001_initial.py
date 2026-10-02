"""initial schema

Creates every upay Shield table, index and constraint.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-02

Enum vocabularies are written out as literals here rather than imported from
``app.models.enums`` on purpose: a migration is an immutable historical record.
Importing the live enum classes would let a future edit silently change what
this revision creates. The values below must mirror ``app.models.enums`` and
the model DDL; ``tests/integration/test_migrations.py`` asserts every table in
``Base.metadata`` is created by this revision.

Enums are stored as ``VARCHAR`` plus a named ``CHECK`` constraint (see the
rationale in ``app.models.enums``). Constraint and index names match the ORM's
metadata naming convention exactly.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---------------------------------------------------------------------------
# Controlled vocabularies (must mirror app.models.enums).
# ---------------------------------------------------------------------------
ENTITY_KINDS = ("customer", "agent", "merchant")
DEVICE_CHANNELS = ("app", "ussd", "agent_terminal", "web", "api")
TRANSACTION_TYPES = (
    "send_money",
    "cash_in",
    "cash_out",
    "merchant_payment",
    "bill_payment",
    "mobile_recharge",
    "agent_settlement",
)
TRANSACTION_STATUSES = ("pending", "completed", "failed", "reversed")
POLICY_LEVELS = ("low", "medium", "high", "insufficient")
RISK_CATEGORIES = (
    "account_takeover",
    "velocity_burst",
    "mule_network",
    "circular_flow",
    "agent_risk",
    "scam_pattern",
    "anomaly",
    "model_risk",
    "policy_review",
)
EVIDENCE_SOURCES = (
    "model",
    "anomaly",
    "graph",
    "agent",
    "scam",
    "policy",
    "device",
    "location",
    "velocity",
    "data_quality",
)
ALERT_SEVERITIES = ("low", "medium", "high", "critical")
ALERT_STATUSES = ("open", "assigned", "in_review", "resolved", "dismissed")
CASE_STATUSES = ("open", "in_review", "awaiting_info", "resolved", "closed")
ANALYST_DISPOSITIONS = (
    "pending",
    "confirmed_fraud",
    "likely_fraud",
    "benign",
    "inconclusive",
    "escalated",
)
CASE_EVENT_TYPES = (
    "created",
    "assigned",
    "unassigned",
    "status_changed",
    "note_added",
    "evidence_attached",
    "explanation_generated",
    "action_confirmed",
    "escalated",
    "resolved",
)
AUDIT_ACTIONS = (
    "created",
    "updated",
    "assigned",
    "status_changed",
    "action_confirmed",
    "explanation_generated",
    "simulation_created",
    "simulation_stepped",
    "simulation_paused",
    "simulation_reset",
    "login",
    "export",
)
SIMULATION_RUN_STATUSES = ("created", "running", "paused", "completed", "failed")


def _enum_length(values: Sequence[str]) -> int:
    """Column length for a CHECK-constrained enum, matching the ORM."""
    return max(len(value) for value in values)


def _in_check(
    table: str,
    column: str,
    values: Sequence[str],
    enum_name: str,
) -> sa.CheckConstraint:
    """Build the CHECK constraint the ORM generates for an enum.

    Alembic applies the target metadata's naming convention, so the name given
    here is the *constraint name token* only; the convention expands it to
    ``ck_<table>_<name>``. Passing the fully qualified name would double the
    prefix.
    """
    joined = ", ".join(f"'{value}'" for value in values)
    return sa.CheckConstraint(
        f"{column} IN ({joined})",
        name=enum_name,
    )


def upgrade() -> None:
    # --- entities ----------------------------------------------------------
    op.create_table(
        "entities",
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=_enum_length(ENTITY_KINDS)), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
        sa.Column("peer_group", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("entity_id", name="pk_entities"),
        _in_check("entities", "kind", ENTITY_KINDS, "entity_kind"),
    )

    # --- devices -----------------------------------------------------------
    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "channel",
            sa.String(length=_enum_length(DEVICE_CHANNELS)),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entities.entity_id"],
            name="fk_devices_entity_id_entities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("device_id", name="pk_devices"),
        _in_check("devices", "channel", DEVICE_CHANNELS, "device_channel"),
    )

    # --- login_events ------------------------------------------------------
    op.create_table(
        "login_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entities.entity_id"],
            name="fk_login_events_entity_id_entities",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
            name="fk_login_events_device_id_devices",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_login_events"),
        sa.CheckConstraint("success IN (true, false)", name="login_success_bool"),
    )

    # --- simulation_runs ---------------------------------------------------
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=False),
        sa.Column("scenario", sa.String(length=64), nullable=False),
        sa.Column("simulated_clock", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=_enum_length(SIMULATION_RUN_STATUSES)),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("events_emitted", sa.Integer(), nullable=False),
        sa.Column("last_step_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_simulation_runs"),
        _in_check(
            "simulation_runs",
            "status",
            SIMULATION_RUN_STATUSES,
            "simulation_run_status",
        ),
    )

    # --- model_versions ----------------------------------------------------
    op.create_table(
        "model_versions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("artifact_checksum", sa.String(length=128), nullable=False),
        sa.Column("dataset_manifest", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("feature_schema_version", sa.String(length=32), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_model_versions"),
        sa.UniqueConstraint(
            "artifact_checksum",
            name="uq_model_versions_artifact_checksum",
        ),
    )

    # --- transactions ------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("sender_id", sa.String(length=64), nullable=False),
        sa.Column("receiver_id", sa.String(length=64), nullable=False),
        sa.Column("amount_poisha", sa.BigInteger(), nullable=False),
        sa.Column(
            "type",
            sa.String(length=_enum_length(TRANSACTION_TYPES)),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("location", sa.String(length=128), nullable=True),
        sa.Column(
            "status",
            sa.String(length=_enum_length(TRANSACTION_STATUSES)),
            nullable=False,
        ),
        sa.Column("scenario_run_id", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["entities.entity_id"],
            name="fk_transactions_sender_id_entities",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["receiver_id"],
            ["entities.entity_id"],
            name="fk_transactions_receiver_id_entities",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.device_id"],
            name="fk_transactions_device_id_devices",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["scenario_run_id"],
            ["simulation_runs.id"],
            name="fk_transactions_scenario_run_id_simulation_runs",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_transactions"),
        sa.UniqueConstraint("idempotency_key", name="uq_transactions_idempotency_key"),
        sa.CheckConstraint("amount_poisha >= 0", name="amount_non_negative"),
        sa.CheckConstraint("sender_id <> receiver_id", name="sender_not_receiver"),
        _in_check("transactions", "type", TRANSACTION_TYPES, "transaction_type"),
        _in_check("transactions", "status", TRANSACTION_STATUSES, "transaction_status"),
    )

    # --- assessments -------------------------------------------------------
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("feature_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("raw_model_score", sa.Float(), nullable=True),
        sa.Column("calibrated_probability", sa.Float(), nullable=True),
        sa.Column("anomaly_percentile", sa.Float(), nullable=True),
        sa.Column(
            "policy_level",
            sa.String(length=_enum_length(POLICY_LEVELS)),
            nullable=False,
        ),
        sa.Column("recommendation", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("processing_ms", sa.Integer(), nullable=True),
        sa.Column(
            "assessed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_assessments_transaction_id_transactions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["model_version"],
            ["model_versions.id"],
            name="fk_assessments_model_version_model_versions",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_assessments"),
        sa.UniqueConstraint(
            "transaction_id",
            "model_version",
            name="uq_assessments_transaction_id_model_version",
        ),
        sa.CheckConstraint(
            "calibrated_probability IS NULL OR "
            "(calibrated_probability >= 0 AND calibrated_probability <= 1)",
            name="calibrated_probability_range",
        ),
        sa.CheckConstraint(
            "anomaly_percentile IS NULL OR "
            "(anomaly_percentile >= 0 AND anomaly_percentile <= 100)",
            name="anomaly_percentile_range",
        ),
        _in_check("assessments", "policy_level", POLICY_LEVELS, "policy_level"),
    )

    # --- evidence ----------------------------------------------------------
    op.create_table(
        "evidence",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("assessment_id", sa.String(length=64), nullable=False),
        sa.Column(
            "source",
            sa.String(length=_enum_length(EVIDENCE_SOURCES)),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("observed_value", sa.String(length=128), nullable=True),
        sa.Column("baseline_value", sa.String(length=128), nullable=True),
        sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provenance", sa.String(length=255), nullable=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessments.id"],
            name="fk_evidence_assessment_id_assessments",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_evidence"),
        _in_check("evidence", "source", EVIDENCE_SOURCES, "evidence_source"),
    )

    # --- alerts ------------------------------------------------------------
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("assessment_id", sa.String(length=64), nullable=False),
        sa.Column(
            "category",
            sa.String(length=_enum_length(RISK_CATEGORIES)),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=_enum_length(ALERT_SEVERITIES)),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=_enum_length(ALERT_STATUSES)),
            nullable=False,
        ),
        sa.Column("assigned_to", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["assessments.id"],
            name="fk_alerts_assessment_id_assessments",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alerts"),
        sa.UniqueConstraint("assessment_id", name="uq_alerts_assessment_id"),
        _in_check("alerts", "category", RISK_CATEGORIES, "risk_category"),
        _in_check("alerts", "severity", ALERT_SEVERITIES, "alert_severity"),
        _in_check("alerts", "status", ALERT_STATUSES, "alert_status"),
    )

    # --- cases -------------------------------------------------------------
    op.create_table(
        "cases",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("alert_id", sa.String(length=64), nullable=False),
        sa.Column("owner", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=_enum_length(CASE_STATUSES)),
            nullable=False,
        ),
        sa.Column(
            "analyst_disposition",
            sa.String(length=_enum_length(ANALYST_DISPOSITIONS)),
            nullable=True,
        ),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("revision", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_cases_alert_id_alerts",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cases"),
        sa.UniqueConstraint("alert_id", name="uq_cases_alert_id"),
        _in_check("cases", "status", CASE_STATUSES, "case_status"),
        _in_check(
            "cases",
            "analyst_disposition",
            ANALYST_DISPOSITIONS,
            "analyst_disposition",
        ),
    )

    # --- case_events -------------------------------------------------------
    op.create_table(
        "case_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("case_id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column(
            "event_type",
            sa.String(length=_enum_length(CASE_EVENT_TYPES)),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["case_id"],
            ["cases.id"],
            name="fk_case_events_case_id_cases",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_case_events"),
        _in_check("case_events", "event_type", CASE_EVENT_TYPES, "case_event_type"),
    )

    # --- audit_events ------------------------------------------------------
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column(
            "action",
            sa.String(length=_enum_length(AUDIT_ACTIONS)),
            nullable=False,
        ),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("object_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("before_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        _in_check("audit_events", "action", AUDIT_ACTIONS, "audit_action"),
    )

    # --- scenario_truth ----------------------------------------------------
    # Synthetic ground truth. Never joined into scoring features.
    op.create_table(
        "scenario_truth",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("scenario_run_id", sa.String(length=64), nullable=True),
        sa.Column("transaction_id", sa.String(length=64), nullable=True),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("scenario", sa.String(length=64), nullable=False),
        sa.Column("is_fraud", sa.Boolean(), nullable=False),
        sa.Column("fraud_family", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["scenario_run_id"],
            ["simulation_runs.id"],
            name="fk_scenario_truth_scenario_run_id_simulation_runs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="fk_scenario_truth_transaction_id_transactions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"],
            ["entities.entity_id"],
            name="fk_scenario_truth_entity_id_entities",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_scenario_truth"),
        sa.UniqueConstraint(
            "transaction_id",
            name="uq_scenario_truth_transaction_id",
        ),
    )

    # --- indexes -----------------------------------------------------------
    op.create_index("ix_entities_kind", "entities", ["kind"])
    op.create_index("ix_entities_kind_region", "entities", ["kind", "region"])
    op.create_index("ix_entities_peer_group", "entities", ["peer_group"])

    op.create_index("ix_devices_entity_channel", "devices", ["entity_id", "channel"])

    op.create_index(
        "ix_login_events_entity_timestamp",
        "login_events",
        ["entity_id", "timestamp"],
    )
    op.create_index("ix_login_events_timestamp", "login_events", ["timestamp"])

    op.create_index("ix_model_versions_trained_at", "model_versions", ["trained_at"])
    op.create_index(
        "ix_model_versions_feature_schema_version",
        "model_versions",
        ["feature_schema_version"],
    )

    op.create_index("ix_transactions_timestamp", "transactions", ["timestamp"])
    op.create_index(
        "ix_transactions_sender_timestamp",
        "transactions",
        ["sender_id", "timestamp"],
    )
    op.create_index(
        "ix_transactions_receiver_timestamp",
        "transactions",
        ["receiver_id", "timestamp"],
    )
    op.create_index(
        "ix_transactions_type_timestamp",
        "transactions",
        ["type", "timestamp"],
    )
    op.create_index(
        "ix_transactions_status_timestamp",
        "transactions",
        ["status", "timestamp"],
    )
    op.create_index(
        "ix_transactions_scenario_run_timestamp",
        "transactions",
        ["scenario_run_id", "timestamp"],
    )

    op.create_index("ix_assessments_transaction_id", "assessments", ["transaction_id"])
    op.create_index(
        "ix_assessments_policy_level_assessed_at",
        "assessments",
        ["policy_level", "assessed_at"],
    )
    op.create_index("ix_assessments_assessed_at", "assessments", ["assessed_at"])

    op.create_index(
        "ix_evidence_assessment_id_ordinal",
        "evidence",
        ["assessment_id", "ordinal"],
    )
    op.create_index("ix_evidence_source_code", "evidence", ["source", "code"])

    op.create_index(
        "ix_alerts_status_severity_created_at",
        "alerts",
        ["status", "severity", "created_at"],
    )
    op.create_index(
        "ix_alerts_severity_created_at",
        "alerts",
        ["severity", "created_at"],
    )
    op.create_index("ix_alerts_status_created_at", "alerts", ["status", "created_at"])
    op.create_index(
        "ix_alerts_assigned_to_status",
        "alerts",
        ["assigned_to", "status"],
    )
    op.create_index(
        "ix_alerts_category_created_at",
        "alerts",
        ["category", "created_at"],
    )

    op.create_index("ix_cases_owner_status", "cases", ["owner", "status"])
    op.create_index("ix_cases_owner_updated_at", "cases", ["owner", "updated_at"])
    op.create_index("ix_cases_status_updated_at", "cases", ["status", "updated_at"])

    op.create_index(
        "ix_case_events_case_id_timestamp",
        "case_events",
        ["case_id", "timestamp"],
    )
    op.create_index(
        "ix_case_events_actor_timestamp",
        "case_events",
        ["actor", "timestamp"],
    )

    op.create_index(
        "ix_audit_events_object",
        "audit_events",
        ["object_type", "object_id", "timestamp"],
    )
    op.create_index(
        "ix_audit_events_actor_timestamp",
        "audit_events",
        ["actor", "timestamp"],
    )
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])

    op.create_index(
        "ix_simulation_runs_status_created_at",
        "simulation_runs",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_simulation_runs_created_by_created_at",
        "simulation_runs",
        ["created_by", "created_at"],
    )
    op.create_index("ix_simulation_runs_scenario", "simulation_runs", ["scenario"])

    op.create_index(
        "ix_scenario_truth_run_scenario",
        "scenario_truth",
        ["scenario_run_id", "scenario"],
    )
    op.create_index(
        "ix_scenario_truth_is_fraud_family",
        "scenario_truth",
        ["is_fraud", "fraud_family"],
    )


def downgrade() -> None:
    op.drop_index("ix_scenario_truth_is_fraud_family", table_name="scenario_truth")
    op.drop_index("ix_scenario_truth_run_scenario", table_name="scenario_truth")
    op.drop_index("ix_simulation_runs_scenario", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_created_by_created_at", table_name="simulation_runs")
    op.drop_index("ix_simulation_runs_status_created_at", table_name="simulation_runs")
    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_request_id", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_object", table_name="audit_events")
    op.drop_index("ix_case_events_actor_timestamp", table_name="case_events")
    op.drop_index("ix_case_events_case_id_timestamp", table_name="case_events")
    op.drop_index("ix_cases_status_updated_at", table_name="cases")
    op.drop_index("ix_cases_owner_updated_at", table_name="cases")
    op.drop_index("ix_cases_owner_status", table_name="cases")
    op.drop_index("ix_alerts_category_created_at", table_name="alerts")
    op.drop_index("ix_alerts_assigned_to_status", table_name="alerts")
    op.drop_index("ix_alerts_status_created_at", table_name="alerts")
    op.drop_index("ix_alerts_severity_created_at", table_name="alerts")
    op.drop_index("ix_alerts_status_severity_created_at", table_name="alerts")
    op.drop_index("ix_evidence_source_code", table_name="evidence")
    op.drop_index("ix_evidence_assessment_id_ordinal", table_name="evidence")
    op.drop_index("ix_assessments_assessed_at", table_name="assessments")
    op.drop_index("ix_assessments_policy_level_assessed_at", table_name="assessments")
    op.drop_index("ix_assessments_transaction_id", table_name="assessments")
    op.drop_index("ix_transactions_scenario_run_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_status_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_type_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_receiver_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_sender_timestamp", table_name="transactions")
    op.drop_index("ix_transactions_timestamp", table_name="transactions")
    op.drop_index("ix_model_versions_feature_schema_version", table_name="model_versions")
    op.drop_index("ix_model_versions_trained_at", table_name="model_versions")
    op.drop_index("ix_login_events_timestamp", table_name="login_events")
    op.drop_index("ix_login_events_entity_timestamp", table_name="login_events")
    op.drop_index("ix_devices_entity_channel", table_name="devices")
    op.drop_index("ix_entities_peer_group", table_name="entities")
    op.drop_index("ix_entities_kind_region", table_name="entities")
    op.drop_index("ix_entities_kind", table_name="entities")

    op.drop_table("scenario_truth")
    op.drop_table("audit_events")
    op.drop_table("case_events")
    op.drop_table("cases")
    op.drop_table("alerts")
    op.drop_table("evidence")
    op.drop_table("assessments")
    op.drop_table("transactions")
    op.drop_table("model_versions")
    op.drop_table("simulation_runs")
    op.drop_table("login_events")
    op.drop_table("devices")
    op.drop_table("entities")
