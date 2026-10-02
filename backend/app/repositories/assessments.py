"""Repositories for persisted assessments and their evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.errors import ValidationFailed
from app.models.assessment import Assessment, Evidence
from app.models.enums import PolicyLevel
from app.repositories.base import BaseRepository, UpsertResult, bounded_limit, ensure_aware
from app.repositories.pagination import Page, PageParams, SortSpec

#: Fields a re-score is allowed to refresh on an existing assessment row.
_MUTABLE_ASSESSMENT_FIELDS = (
    "feature_snapshot",
    "schema_version",
    "raw_model_score",
    "calibrated_probability",
    "anomaly_percentile",
    "policy_level",
    "recommendation",
    "policy_version",
    "processing_ms",
    "assessed_at",
)


@dataclass(frozen=True)
class PolicyLevelCount:
    """Row count for one policy level."""

    policy_level: PolicyLevel
    count: int


class AssessmentRepository(BaseRepository[Assessment]):
    """Data access for scoring decisions."""

    model = Assessment

    SORTABLE: Mapping[str, Any] = {
        "assessed_at": Assessment.assessed_at,
        "id": Assessment.id,
        "policy_level": Assessment.policy_level,
        "raw_model_score": Assessment.raw_model_score,
    }

    def get_with_evidence(self, assessment_id: str) -> Assessment | None:
        """Fetch an assessment with its ordered evidence eager-loaded."""
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .options(selectinload(Assessment.evidence))
        )
        return self.session.scalars(stmt).first()

    def get_latest_for_transaction(self, transaction_id: str) -> Assessment | None:
        """Return the most recent assessment for a transaction, or ``None``.

        A transaction may have been scored under more than one model version;
        the latest by ``assessed_at`` (then id) wins.
        """
        return self.session.scalars(
            select(Assessment)
            .where(Assessment.transaction_id == transaction_id)
            .order_by(Assessment.assessed_at.desc(), Assessment.id.desc())
            .limit(1)
        ).first()

    def get_for_transaction_model(
        self,
        transaction_id: str,
        model_version: str | None,
    ) -> Assessment | None:
        """Return the assessment for a ``(transaction, model)`` pair.

        ``IS NULL`` is used for ``model_version`` because PostgreSQL treats
        NULLs as distinct in a unique index; without this a degraded assessment
        would never be found again.
        """
        stmt = select(Assessment).where(Assessment.transaction_id == transaction_id)
        if model_version is None:
            stmt = stmt.where(Assessment.model_version.is_(None))
        else:
            stmt = stmt.where(Assessment.model_version == model_version)
        return self.session.scalars(stmt.limit(1)).first()

    def upsert(self, assessment: Assessment) -> UpsertResult[Assessment]:
        """Insert or refresh an assessment for ``(transaction, model_version)``.

        Idempotent for a retried score: the existing row is updated in place
        (and its evidence replaced by the caller) rather than duplicated.
        """
        existing = self.get_for_transaction_model(
            assessment.transaction_id, assessment.model_version
        )
        if existing is not None:
            for field in _MUTABLE_ASSESSMENT_FIELDS:
                setattr(existing, field, getattr(assessment, field))
            self.session.flush()
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(assessment)
        except IntegrityError:
            existing = self.get_for_transaction_model(
                assessment.transaction_id, assessment.model_version
            )
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(assessment, True)

    def add_evidence(
        self,
        assessment_id: str,
        items: Sequence[Evidence],
    ) -> Sequence[Evidence]:
        """Attach evidence rows to an assessment in one flush."""
        for item in items:
            item.assessment_id = assessment_id
            self.session.add(item)
        self.session.flush()
        return list(items)

    def replace_evidence(
        self,
        assessment_id: str,
        items: Sequence[Evidence],
    ) -> Sequence[Evidence]:
        """Replace all evidence for an assessment (used on a re-score)."""
        self.session.execute(
            Evidence.__table__.delete().where(Evidence.assessment_id == assessment_id)
        )
        return self.add_evidence(assessment_id, items)

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        policy_level: PolicyLevel | None = None,
        transaction_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Page[Assessment]:
        """Paginated, filtered assessment list."""
        stmt: Select[Any] = select(Assessment)
        if policy_level is not None:
            stmt = stmt.where(Assessment.policy_level == policy_level)
        if transaction_id is not None:
            stmt = stmt.where(Assessment.transaction_id == transaction_id)
        if since is not None:
            stmt = stmt.where(
                Assessment.assessed_at >= ensure_aware(since, name="since")
            )
        if until is not None:
            stmt = stmt.where(
                Assessment.assessed_at < ensure_aware(until, name="until")
            )
        return self._paginate(stmt, params, sort, self.SORTABLE)

    def count_by_policy_level(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[PolicyLevelCount]:
        """Assessment counts grouped by policy level (database aggregate)."""
        stmt = select(Assessment.policy_level, func.count()).group_by(
            Assessment.policy_level
        )
        if start is not None:
            stmt = stmt.where(Assessment.assessed_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Assessment.assessed_at < ensure_aware(end, name="end"))
        rows = self.session.execute(stmt).all()
        return [
            PolicyLevelCount(policy_level=row[0], count=int(row[1])) for row in rows
        ]

    def count_scored(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        distinct_transactions: bool = True,
    ) -> int:
        """Count assessments (or distinct scored transactions) in a window."""
        column = (
            func.count(func.distinct(Assessment.transaction_id))
            if distinct_transactions
            else func.count()
        )
        stmt = select(column)
        if start is not None:
            stmt = stmt.where(Assessment.assessed_at >= ensure_aware(start, name="start"))
        if end is not None:
            stmt = stmt.where(Assessment.assessed_at < ensure_aware(end, name="end"))
        return int(self.session.scalar(stmt) or 0)


class EvidenceRepository(BaseRepository[Evidence]):
    """Reads and writes for individual evidence rows."""

    model = Evidence

    SORTABLE: Mapping[str, Any] = {
        "ordinal": Evidence.ordinal,
        "created_at": Evidence.created_at,
        "id": Evidence.id,
    }

    def list_for_assessment(
        self,
        assessment_id: str,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[Evidence]:
        """Ordered evidence for an assessment, bounded and deterministic."""
        bounded = bounded_limit(limit, default=200, maximum=500)
        return list(
            self.session.scalars(
                select(Evidence)
                .where(Evidence.assessment_id == assessment_id)
                .order_by(Evidence.ordinal.asc(), Evidence.id.asc())
                .limit(bounded)
                .offset(offset)
            ).all()
        )

    def add_many(self, items: Sequence[Evidence]) -> Sequence[Evidence]:
        """Stage several evidence rows; caller controls the transaction."""
        if not items:
            raise ValidationFailed("At least one evidence row is required.")
        self.session.add_all(list(items))
        self.session.flush()
        return list(items)

    def delete_for_assessment(self, assessment_id: str) -> int:
        """Delete all evidence for an assessment; returns rows removed."""
        result = self.session.execute(
            Evidence.__table__.delete().where(Evidence.assessment_id == assessment_id)
        )
        return int(result.rowcount or 0)
