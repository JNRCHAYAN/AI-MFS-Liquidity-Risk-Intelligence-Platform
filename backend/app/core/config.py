"""Application configuration.

All settings come from the environment. `.env.example` documents every
variable name and its purpose; no real value is ever committed.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Repository root, derived from this file's location:
#: backend/app/core/config.py -> core -> app -> backend -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]

# The business timezone. Behavioural hour/day features are derived in this zone
# consistently between training and inference. Storage is always UTC.
BUSINESS_TIMEZONE = "Asia/Dhaka"

# The feature schema version shared by training and inference. A model artifact
# whose recorded version differs from this value must fail readiness.
FEATURE_SCHEMA_VERSION = "1.0.0"

# Policy routing version. Thresholds are set from validation, not defaults.
# See docs/architecture.md section 7.
POLICY_VERSION = "1.0.0"


class Settings(BaseSettings):
    """Runtime configuration for the API service."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Runtime -----------------------------------------------------------
    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Database ----------------------------------------------------------
    # No default: the service must not silently fall back to an unintended
    # datastore. Readiness reports unavailable when this is unset.
    database_url: str | None = None

    # --- Authentication ----------------------------------------------------
    supabase_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str | None = "authenticated"
    supabase_service_role_key: str | None = None

    # --- CORS --------------------------------------------------------------
    # Exact allowlist of frontend origins. CORS is not authentication.
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Model bundle ------------------------------------------------------
    model_bundle_path: str = "ml/artifacts"

    # --- Demo protection ---------------------------------------------------
    # When true, the public seed demo is immutable and mutation APIs are closed.
    demo_read_only: bool = True

    # --- Optional LLM ------------------------------------------------------
    # The product must remain fully functional with these unset.
    gemini_api_key: str | None = None
    gemini_model: str | None = None

    # --- Derived helpers ---------------------------------------------------

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string from the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def model_bundle_dir(self) -> Path:
        """Absolute path to the model bundle.

        A relative ``MODEL_BUNDLE_PATH`` is resolved against the repository
        root, not the process working directory. Without this, running the API
        from ``backend/`` would look for ``backend/ml/artifacts`` while running
        it from the repository root would find ``ml/artifacts`` — the same
        configuration silently pointing at two different places.
        """
        path = Path(self.model_bundle_path)
        return path if path.is_absolute() else (REPO_ROOT / path)

    @property
    def llm_enabled(self) -> bool:
        """Whether optional LLM narrative generation is configured."""
        return bool(self.gemini_api_key and self.gemini_model)

    @property
    def auth_configured(self) -> bool:
        """Whether token verification can be performed at all."""
        return bool(self.supabase_jwt_issuer and self.supabase_jwt_audience)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so the environment is read once per process. Tests clear the cache
    via `get_settings.cache_clear()` when overriding the environment.
    """
    return Settings()
