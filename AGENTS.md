# AGENTS.md — working instructions for AI coding agents

This repository is an entry for **AI DEV FEST 2026 — AI Hackathon, Track 01
(Trust & Risk Intelligence)**, organized by DIU CPC × upay. The product is
called **upay Shield**.

Read this file, `docs/requirements-traceability.md` and `docs/PROGRESS.md`
before making changes.

## Non-negotiable rules

1. **Synthetic data only.** Never introduce real customer data, real PII or
   production upay data. Every displayed record must be clearly synthetic.
2. **Never invent facts.** Do not fabricate secrets, credentials, live URLs,
   commit SHAs, push results, official deadlines, model metrics, or test
   outcomes. If something is unknown or blocked, record it as unknown or
   blocked and continue with independent local work.
3. **No new real-money behaviour.** Hold / release / verify / block actions
   operate *only* inside the synthetic simulation. Never integrate a real
   payment, lending or upay production API.
4. **The LLM is never the authority.** Gemini may generate narrative text
   only. It must never decide fraud, move money, or authorize an action.
5. **Continuous history.** Commit each completed increment with a meaningful
   Conventional Commit message. Do not squash away the development history
   and do not force-push.
6. **Never fabricate a metric.** If the model performs poorly, report the
   real number. See `docs/model-card.md`.

## Architecture summary

Modular monolith: one FastAPI service, one Next.js application, PostgreSQL.
No multi-agent runtime. Inference is separate from training.

```text
backend/   FastAPI service — thin routes, services hold decisions,
           repositories hold SQL, intelligence/ holds model inference
frontend/  Next.js App Router — TypeScript strict, Tailwind
ml/        Offline pipeline — generate, featurise, train, evaluate, package
docs/      Compliance, model, evaluation and deployment documentation
```

## Engineering conventions

- **Money** is stored as integer **poisha**. Never use a binary float for a
  ledger quantity. Format to BDT/৳ only at the display layer.
- **Timestamps** are stored in UTC and rendered in `Asia/Dhaka` with the
  timezone shown. Behavioural hour/day features are derived in `Asia/Dhaka`
  consistently between training and inference.
- **Causality is mandatory.** Every feature window uses events *strictly
  preceding* the scored transaction, with deterministic tie-breaking for
  equal timestamps. Never use future transactions, final resolution status,
  fraud labels, or later analyst decisions as evidence.
- **One feature schema** is shared by training and inference. It is versioned;
  a mismatch between a model artifact and the live schema must fail readiness.
- **Contract first.** Define the OpenAPI schema before the UI that consumes
  it. Frontend API types are generated from OpenAPI, not hand-maintained.
- No silent broad exception handlers, no untyped arbitrary payloads, no
  fabricated fallback success, no speculative TODO-driven features.

## Workflow for each increment

1. Implement the change.
2. Run the relevant checks (lint, typecheck, tests).
3. Update `README.md`, `docs/requirements-traceability.md` and
   `docs/PROGRESS.md`.
4. Inspect `git diff` for secrets, accidental data and unrelated edits.
5. Stage specific intended paths (never `git add -A` blindly), commit, push.
6. Verify the push: `git rev-parse HEAD` must match the remote branch SHA.
7. Record the SHA and push result in `docs/PROGRESS.md`.

## Verification commands

| Command | Purpose |
|---|---|
| `cd backend && .venv/Scripts/python -m pytest` | Backend unit + integration tests |
| `cd backend && .venv/Scripts/python -m ruff check .` | Backend lint |
| `cd frontend && npm run lint` | Frontend lint |
| `cd frontend && npm run typecheck` | Frontend type check |
| `cd frontend && npm run build` | Frontend production build |
| `cd frontend && npm run test:e2e` | Playwright end-to-end flows |

Windows uses `.venv/Scripts/`; POSIX systems use `.venv/bin/`.

## Honest-state requirements

The UI and API must distinguish **loading**, **empty**, **error** and
**degraded/unavailable** states. When a model artifact or the database is
unavailable, return an explicit unavailable error — never invent a score.

## Documentation obligations

| File | Contents |
|---|---|
| `docs/PROGRESS.md` | Current stage, SHAs, blockers, next step |
| `docs/requirements-traceability.md` | Official requirement → evidence map |
| `docs/data-card.md` | Synthetic data scope and assumptions |
| `docs/model-card.md` | Model design, metrics, limitations |
| `docs/evaluation.md` | Held-out results vs baseline |
| `docs/threat-model.md` | Adversarial and access-control analysis |
| `docs/ai-disclosure.md` | AI tools and components used |
| `docs/onsite-changes.md` | On-site change log |
