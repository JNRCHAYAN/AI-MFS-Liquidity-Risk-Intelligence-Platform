"""Data-access layer for upay Shield.

All SQL lives under this package. Services and routes depend on these classes,
never on a session or a query directly.

Every list method is paginated and bounded; every causal read is explicit about
its time boundary. See :mod:`app.repositories.transactions` for the feature
engine's causality contract.
"""

from __future__ import annotations

from app.repositories.alerts import (
    AlertRepository,
    CaseEventRepository,
    CaseRepository,
)
from app.repositories.analytics import (
    DashboardOverview,
    DashboardRepository,
    DayCount,
    TypeCount,
)
from app.repositories.assessments import (
    AssessmentRepository,
    EvidenceRepository,
    PolicyLevelCount,
)
from app.repositories.audit import AuditEventRepository
from app.repositories.base import BaseRepository, UpsertResult
from app.repositories.entities import (
    DeviceRepository,
    EntityRepository,
    KindCount,
    LoginEventRepository,
)
from app.repositories.model_registry import ModelVersionRepository
from app.repositories.pagination import (
    DEFAULT_PAGE_LIMIT,
    MAX_PAGE_LIMIT,
    Page,
    PageParams,
    SortOrder,
    SortSpec,
)
from app.repositories.session import (
    database_is_ready,
    get_engine,
    get_sessionmaker,
    session_scope,
)
from app.repositories.simulation import (
    EvaluationTruthCounts,
    RunResetResult,
    ScenarioTruthRepository,
    SimulationRunRepository,
)
from app.repositories.transactions import (
    Direction,
    TransactionAmountStats,
    TransactionFilters,
    TransactionRepository,
)

__all__ = [
    "DEFAULT_PAGE_LIMIT",
    "MAX_PAGE_LIMIT",
    "AlertRepository",
    "AssessmentRepository",
    "AuditEventRepository",
    "BaseRepository",
    "CaseEventRepository",
    "CaseRepository",
    "DashboardOverview",
    "DashboardRepository",
    "DayCount",
    "DeviceRepository",
    "Direction",
    "EntityRepository",
    "EvaluationTruthCounts",
    "EvidenceRepository",
    "KindCount",
    "LoginEventRepository",
    "ModelVersionRepository",
    "Page",
    "PageParams",
    "PolicyLevelCount",
    "RunResetResult",
    "ScenarioTruthRepository",
    "SimulationRunRepository",
    "SortOrder",
    "SortSpec",
    "TransactionAmountStats",
    "TransactionFilters",
    "TransactionRepository",
    "TypeCount",
    "UpsertResult",
    "database_is_ready",
    "get_engine",
    "get_sessionmaker",
    "session_scope",
]
