# upay Shield — Trust & Risk Intelligence

> **Hackathon prototype. No real transactions.**
> Built for **AI DEV FEST 2026 — AI Hackathon, Track 01 (Trust & Risk
> Intelligence)**, organized by DIU CPC × upay.
>
> "upay Shield" is a proposed hackathon concept. It is **not** an official upay
> product and makes no partnership claim. All data is synthetic.

---

## Project overview

**The problem.** Fraud analysts at a mobile financial service (MFS) see
fragmented signals. A suspicious transaction sits alongside device history,
login failures, peer-agent behaviour and network structure, but nothing joins
them up. The analyst cannot quickly answer three questions: *what happened*,
*why is it risky*, and *what should be done next*.

**The solution.** upay Shield combines a trained tabular classifier, a
behavioural anomaly score, time-bounded transaction-graph evidence and
explicit versioned policy rules into a single explained alert with a
recommended review action and an accountable analyst workflow.

**Primary user.** Fraud analyst. **Secondary.** Risk manager, hackathon judge.
Customers, merchants and agents are simulated entities, not real account
holders.

**Read next:** [`docs/architecture.md`](docs/architecture.md),
[`docs/requirements-traceability.md`](docs/requirements-traceability.md).

---

## Implemented features

> **Status: scaffolding in progress.** This table is updated as each stage
> completes. Anything marked *planned* is **not** implemented yet — see
> [`docs/PROGRESS.md`](docs/PROGRESS.md) for the authoritative stage status.

| Track 01 direction | Status |
|---|---|
| Real-time transaction risk (XGBoost) | Planned |
| Behavioural anomaly detection (Isolation Forest) | Planned |
| Account takeover evidence | Planned |
| Money-mule / network risk (graph motifs) | Planned |
| Agent risk (peer-relative deviation) | Planned |
| Scam pattern intelligence | Planned |
| AI investigation assistant (evidence-grounded) | Planned |

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), TypeScript strict, Tailwind CSS, TanStack Query, Recharts, React Flow |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Intelligence | pandas, NumPy, scikit-learn, XGBoost, SHAP, NetworkX |
| Database | PostgreSQL (Supabase managed, or Render Postgres) |
| Auth | Supabase Auth, JWKS-verified server-side |
| LLM (optional) | Google Gemini, backend-only, narrative only |
| Delivery | Docker, Render, GitHub Actions CI |

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11 or 3.12 | Exact verified version recorded in `docs/PROGRESS.md` |
| Node.js | 20+ | For the Next.js frontend |
| PostgreSQL | 15+ | Local via Docker Compose, or managed |
| Docker + Compose | Current | For local database and container builds |

> **Environment note.** The machine this was developed on had Python 3.14 and
> a stopped Docker daemon; both are tracked as limitations in
> `docs/PROGRESS.md`. Do not assume the versions above are what was locally
> verified — that file is authoritative.

---

## Installation and setup

> Filled in as the corresponding stages land. Commands will be verified before
> being documented here — none are placeholders for working code.

```bash
# 1. Clone
git clone <repository-url>
cd <repository>

# 2. Backend
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev]"   # POSIX

# 3. Environment
cp .env.example .env    # then fill in real values

# 4. Frontend
cd ../frontend
npm install
```

## Environment variables

All names, purposes and placeholder values are documented in
[`.env.example`](.env.example). **Never commit real credentials.**

Key groups: database (`DATABASE_URL`), auth (`SUPABASE_*`), CORS
(`CORS_ORIGINS`), model bundle (`MODEL_BUNDLE_PATH`), demo protection
(`DEMO_READ_ONLY`), optional LLM (`GEMINI_*`), and frontend build-time
`NEXT_PUBLIC_*` values.

## Run and build commands

> Filled in and verified per stage.

```bash
# Local database (requires the Docker daemon running)
docker compose up -d db

# Migrations
cd backend && .venv/Scripts/python -m alembic upgrade head

# API (development)
cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload

# Frontend (development)
cd frontend && npm run dev

# Frontend production build
cd frontend && npm run build
```

## Live deployment

**Not deployed.** No live URL exists yet. Any URL will be recorded here only
after it has been verified reachable. See
[`docs/deployment-render.md`](docs/deployment-render.md).

## Testing

```bash
cd backend  && .venv/Scripts/python -m pytest      # backend tests
cd backend  && .venv/Scripts/python -m ruff check . # lint
cd frontend && npm run lint                         # frontend lint
cd frontend && npm run typecheck                    # types
cd frontend && npm run test:e2e                     # Playwright flows
```

> Commands are documented here as they are implemented and verified. See
> `docs/PROGRESS.md` for what has actually been run.

---

## Data and responsible AI

- **Synthetic data only.** No production upay data and no real PII is used.
  See [`docs/data-card.md`](docs/data-card.md).
- **Explainability.** Alerts show signed feature attributions with their units,
  plus policy rules and graph evidence as separate, traceable sources.
- **Human oversight.** Every hold/release/verify/block action is *simulated*,
  requires an authorised analyst and a rationale, and writes an audit event.
- **No autonomous consequential decisions.** The system recommends; a human
  decides.
- **Honest reporting.** Model performance is reported from held-out synthetic
  data, including where it is weak. Synthetic results demonstrate simulator
  behaviour, not real-bank effectiveness.

See [`docs/model-card.md`](docs/model-card.md),
[`docs/evaluation.md`](docs/evaluation.md) and
[`docs/threat-model.md`](docs/threat-model.md).

## Team and attribution

| Member | Role | Status |
|---|---|---|
| `[TO CONFIRM]` | ML, data pipeline | Not yet recorded |
| `[TO CONFIRM]` | Backend, API, auth, deployment | Not yet recorded |
| `[TO CONFIRM]` | Frontend, UI, demo materials | Not yet recorded |

AI tools, third-party libraries, datasets and services are disclosed in
[`docs/ai-disclosure.md`](docs/ai-disclosure.md), as required by Rulebook §4.4
and General Rules §5.6.

## Deployment

Render deployment instructions, the configuration contract and troubleshooting
are in [`docs/deployment-render.md`](docs/deployment-render.md).

## Repository layout

```text
backend/    FastAPI service — routes, services, repositories, intelligence
frontend/   Next.js App Router application
ml/         Synthetic generator, featurisation, training, evaluation, artifacts
data/       Small sample fixtures and generator manifests (not bulk data)
contracts/  Generated OpenAPI contract
docs/       Compliance, model, evaluation, security and deployment docs
```

## Licence and status

Hackathon prototype. Not for production use. No real financial decisions are
made or executed by this software.
