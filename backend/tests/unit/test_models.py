"""Metadata-level tests for the ORM models.

These run without a database. They assert the invariants the build plan
requires: money is integer poisha, timestamps are timezone-aware, mandatory
indexes exist, enums are CHECK-constrained with lowercase values, case updates
use optimistic concurrency, and synthetic ground truth is structurally
isolated from scoring.
"""

from __future__ import annotations

import re

import app.models as models
import pytest
from app.models import Base
from sqlalchemy import BigInteger, DateTime, Float, Numeric, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateTable

EXPECTED_TABLES = {
    "entities",
    "devices",
    "login_events",
    "transactions",
    "assessments",
    "evidence",
    "alerts",
    "cases",
    "case_events",
    "audit_events",
    "simulation_runs",
    "model_versions",
    "scenario_truth",
}

#: Index names the build plan marks mandatory.
MANDATORY_INDEXES = {
    "ix_transactions_timestamp",
    "ix_transactions_sender_timestamp",
    "ix_transactions_receiver_timestamp",
    "ix_alerts_status_severity_created_at",
    "ix_cases_owner_status",
}


@pytest.fixture(scope="module", autouse=True)
def _configure() -> None:
    configure_mappers()


def _all_index_names() -> set[str]:
    names: set[str] = set()
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            if index.name:
                names.add(index.name)
    return names


def test_every_expected_table_is_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_model_registry_lists_all_models() -> None:
    assert {model.__tablename__ for model in models.ALL_MODELS} == EXPECTED_TABLES


def test_money_columns_are_biginteger_not_float() -> None:
    amount = Base.metadata.tables["transactions"].c.amount_poisha
    assert isinstance(amount.type, BigInteger)
    # A float or Numeric money column would be a contract violation.
    assert not isinstance(amount.type, (Float, Numeric))


def test_every_datetime_column_is_timezone_aware() -> None:
    offenders: list[str] = []
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, DateTime) and not column.type.timezone:
                offenders.append(f"{table.name}.{column.name}")
    assert not offenders, f"Naive (non-tz) datetime columns: {offenders}"


def test_mandatory_indexes_exist() -> None:
    assert _all_index_names() >= MANDATORY_INDEXES


def test_mandatory_indexes_exist_in_transactions() -> None:
    names = {index.name for index in Base.metadata.tables["transactions"].indexes}
    assert {
        "ix_transactions_timestamp",
        "ix_transactions_sender_timestamp",
        "ix_transactions_receiver_timestamp",
    } <= names


def test_dedup_unique_constraints_present() -> None:
    def unique_names(table_name: str) -> set[str]:
        table = Base.metadata.tables[table_name]
        return {
            constraint.name
            for constraint in table.constraints
            if constraint.__class__.__name__ == "UniqueConstraint"
        }

    assert "uq_transactions_idempotency_key" in unique_names("transactions")
    assert "uq_assessments_transaction_id_model_version" in unique_names("assessments")
    assert "uq_alerts_assessment_id" in unique_names("alerts")
    assert "uq_cases_alert_id" in unique_names("cases")
    assert "uq_scenario_truth_transaction_id" in unique_names("scenario_truth")


def test_enum_check_constraints_use_lowercase_values() -> None:
    ddl = str(
        CreateTable(Base.metadata.tables["entities"]).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "'customer'" in ddl
    assert "'agent'" in ddl
    assert "'merchant'" in ddl
    # Member NAMES must not leak into the database vocabulary.
    assert "'CUSTOMER'" not in ddl

    txn_ddl = str(
        CreateTable(Base.metadata.tables["transactions"]).compile(
            dialect=postgresql.dialect()
        )
    )
    assert "'send_money'" in txn_ddl
    assert "'SEND_MONEY'" not in txn_ddl


def test_no_double_prefixed_check_constraint_names() -> None:
    """The metadata naming convention must produce ck_<table>_<name> exactly once."""
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if constraint.__class__.__name__ == "CheckConstraint" and constraint.name:
                assert not re.search(r"_ck_[a-z]", constraint.name), constraint.name
                if constraint.name.startswith("ck_"):
                    assert constraint.name.startswith(f"ck_{table.name}_"), constraint.name


def test_cases_use_optimistic_concurrency_column() -> None:
    mapper = inspect(models.Case)
    assert mapper.version_id_col is not None
    assert mapper.version_id_col.name == "revision"


def test_relationships_are_lazy_raise() -> None:
    """Every relationship must fail loudly on accidental lazy load."""
    for model in models.ALL_MODELS:
        mapper = inspect(model)
        for relationship in mapper.relationships:
            assert relationship.lazy == "raise", (
                f"{model.__name__}.{relationship.key} is lazy={relationship.lazy!r}; "
                "all relationships must be lazy='raise' so repositories eager-load "
                "explicitly and never trigger unbounded queries."
            )


def test_scenario_truth_is_structurally_isolated_from_scoring() -> None:
    """Ground truth has no ORM relationship into transactions or assessments."""
    mapper = inspect(models.ScenarioTruth)
    assert list(mapper.relationships) == []
    # And it is not reachable by traversal from the scoring aggregates.
    for model in (models.Transaction, models.Assessment, models.Alert, models.Case):
        related = {rel.mapper.class_.__name__ for rel in inspect(model).relationships}
        assert "ScenarioTruth" not in related


def test_scenario_truth_repository_methods_are_evaluation_prefixed() -> None:
    import inspect

    from app.repositories.base import BaseRepository
    from app.repositories.simulation import ScenarioTruthRepository

    # Only real functions count. Class attributes such as `model` (a class,
    # hence technically callable) and properties such as `session` are not
    # methods and must not be swept into this rule.
    public = [
        name
        for name in dir(ScenarioTruthRepository)
        if not name.startswith("_")
        and inspect.isfunction(getattr(ScenarioTruthRepository, name, None))
    ]
    our_methods = [name for name in public if name.startswith("evaluation_")]
    assert our_methods, "expected evaluation_* methods on ScenarioTruthRepository"

    # Generic CRUD helpers inherited from BaseRepository are exempt: the rule
    # governs the methods this repository adds for touching synthetic ground
    # truth, not inherited plumbing. Derived from BaseRepository rather than
    # hard-coded so the exemption cannot silently drift when the base class
    # gains a method.
    inherited = {
        name
        for name in dir(BaseRepository)
        if inspect.isfunction(getattr(BaseRepository, name, None))
    }

    for name in public:
        if name in inherited:
            continue
        assert name.startswith("evaluation_"), (
            f"ScenarioTruthRepository.{name} must be prefixed 'evaluation_' to "
            "make its offline-only purpose explicit at every call site."
        )
