"""Repository for registered model artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError

from app.models.model_registry import ModelVersion
from app.repositories.base import BaseRepository, UpsertResult
from app.repositories.pagination import Page, PageParams, SortSpec


class ModelVersionRepository(BaseRepository[ModelVersion]):
    """Reads and registration for model versions."""

    model = ModelVersion

    SORTABLE: Mapping[str, Any] = {
        "trained_at": ModelVersion.trained_at,
        "id": ModelVersion.id,
    }

    def get_by_checksum(self, artifact_checksum: str) -> ModelVersion | None:
        """Return the artifact registered under this checksum, if any."""
        return self.session.scalars(
            select(ModelVersion)
            .where(ModelVersion.artifact_checksum == artifact_checksum)
            .limit(1)
        ).first()

    def create(self, model_version: ModelVersion) -> UpsertResult[ModelVersion]:
        """Register an artifact idempotently on its checksum."""
        existing = self.get_by_checksum(model_version.artifact_checksum)
        if existing is not None:
            return UpsertResult(existing, False)
        try:
            with self.session.begin_nested():
                self.session.add(model_version)
        except IntegrityError:
            existing = self.get_by_checksum(model_version.artifact_checksum)
            if existing is None:
                raise
            return UpsertResult(existing, False)
        return UpsertResult(model_version, True)

    def get_current(self) -> ModelVersion | None:
        """Return the most recently trained registered artifact."""
        return self.session.scalars(
            select(ModelVersion)
            .order_by(ModelVersion.trained_at.desc(), ModelVersion.id.desc())
            .limit(1)
        ).first()

    def exists_checksum(self, artifact_checksum: str) -> bool:
        """Whether an artifact with this checksum is registered."""
        return self.get_by_checksum(artifact_checksum) is not None

    def list_page(
        self,
        params: PageParams,
        sort: SortSpec,
        *,
        feature_schema_version: str | None = None,
    ) -> Page[ModelVersion]:
        """Paginated model-version list."""
        stmt: Select[Any] = select(ModelVersion)
        if feature_schema_version is not None:
            stmt = stmt.where(
                ModelVersion.feature_schema_version == feature_schema_version
            )
        return self._paginate(stmt, params, sort, self.SORTABLE)
