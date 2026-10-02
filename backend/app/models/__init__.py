"""SQLAlchemy ORM models for upay Shield.

Importing this package registers every table on :data:`app.models.base.Base`.
Alembic's ``env.py`` imports it (via ``target_metadata``) so autogenerate sees
the complete schema — do not remove any import below.

Money is integer poisha; timestamps are timezone-aware UTC; enums are stored
as strings with CHECK constraints (see :mod:`app.models.enums`).
"""

from __future__ import annotations

from app.models.alert import Alert, Case, CaseEvent
from app.models.assessment import Assessment, Evidence
from app.models.audit import AuditEvent
from app.models.base import Base
from app.models.entity import Device, Entity, LoginEvent
from app.models.model_registry import ModelVersion
from app.models.simulation import ScenarioTruth, SimulationRun
from app.models.transaction import Transaction

#: Every mapped class, for tests and metadata assertions.
ALL_MODELS = (
    Entity,
    Device,
    LoginEvent,
    Transaction,
    Assessment,
    Evidence,
    Alert,
    Case,
    CaseEvent,
    AuditEvent,
    SimulationRun,
    ModelVersion,
    ScenarioTruth,
)

__all__ = [
    "ALL_MODELS",
    "Alert",
    "Assessment",
    "AuditEvent",
    "Base",
    "Case",
    "CaseEvent",
    "Device",
    "Entity",
    "Evidence",
    "LoginEvent",
    "ModelVersion",
    "ScenarioTruth",
    "SimulationRun",
    "Transaction",
]
