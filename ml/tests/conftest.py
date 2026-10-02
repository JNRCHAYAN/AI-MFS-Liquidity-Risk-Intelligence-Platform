"""Shared pytest fixtures for the ml/ test-suite.

Adds the repository root and the ``backend`` package directory to ``sys.path``
so tests can import ``ml.*`` and the frozen feature contract directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

for candidate in (REPO_ROOT, BACKEND_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from ml.scenarios import SimConfig, World, build_world  # noqa: E402


@pytest.fixture(scope="session")
def small_config() -> SimConfig:
    """A deterministic, fast configuration shared by most tests."""
    return SimConfig.small(seed=101)


@pytest.fixture(scope="session")
def world(small_config: SimConfig) -> World:
    """One generated world reused across tests (generation is the slow part)."""
    return build_world(small_config)


@pytest.fixture(scope="session")
def medium_world() -> World:
    """A larger world used for distribution/overlap assertions.

    Larger than the ``--small`` preset so that percentiles are meaningful, but
    still fast enough for a test run.
    """
    return build_world(
        SimConfig(
            seed=2026,
            n_wallets=220,
            n_merchants=16,
            n_agents=9,
            n_transactions=9_000,
            days=45,
        )
    )
