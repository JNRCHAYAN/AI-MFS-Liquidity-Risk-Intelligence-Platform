"""Version 1 API router.

Every application route is mounted here so the version prefix is declared in
exactly one place. Routers are added as their stages land.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()

# Routes are registered here as each implementation stage lands:
#   transactions, alerts, cases, network, agents, models, simulation, dashboard
#
# Intentionally empty for now rather than exposing placeholder endpoints that
# return fabricated data.
