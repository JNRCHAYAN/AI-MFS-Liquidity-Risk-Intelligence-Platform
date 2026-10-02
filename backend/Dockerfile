# Backend image for upay Shield.
#
# Multi-stage build, non-root runtime, no embedded secrets.
# Build context is the repository ROOT so the image can include ml/ artifacts:
#   docker build -f backend/Dockerfile -t shield-api .

# ---------------------------------------------------------------------------
# Stage 1 — dependency build
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Build tooling for any dependency without a manylinux wheel.
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./backend/pyproject.toml

# Install into a virtualenv we can copy wholesale into the runtime stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip \
    && pip install ./backend

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# Run as a non-root user.
RUN groupadd --system --gid 1001 shield \
    && useradd --system --uid 1001 --gid shield --create-home shield

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Application code.
COPY --chown=shield:shield backend/app ./app
COPY --chown=shield:shield backend/alembic.ini ./alembic.ini
COPY --chown=shield:shield backend/migrations ./migrations

# Verified, checksummed model bundle. Small artifacts are embedded in the image
# deliberately: Render's default filesystem is ephemeral, so model state must
# never be written at runtime.
COPY --chown=shield:shield ml/artifacts ./ml-artifacts

USER shield

EXPOSE 8000

# Render provides PORT at runtime. Default to 8000 for local runs.
ENV PORT=8000

# Exec form so the process receives termination signals directly.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
