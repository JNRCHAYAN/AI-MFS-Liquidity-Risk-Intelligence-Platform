# Architecture — upay Shield

## 1. Problem and users

**Problem.** For MFS fraud analysts, fragmented transaction and behavioural
signals make suspicious activity difficult to prioritise and investigate.
Evidence is spread across raw transactions, device and login history, peer
behaviour and network structure, so an analyst cannot quickly answer: what
happened, why is it risky, and what should be done next.

**Primary user.** Fraud analyst. **Secondary.** Risk manager; hackathon judge.
Customers, merchants and agents are *simulated* entities, not real account
holders.

**Solution.** upay Shield combines a tabular ML classifier, a behavioural
anomaly score, transaction-graph evidence and explicit versioned policy rules
to produce an explained alert and a recommended review action.

Every alert must answer three questions:

1. **What happened?** Transaction, timeline, involved entities, behaviour change.
2. **Why is it risky?** Model attribution, anomaly evidence, graph motifs,
   rules — each with provenance.
3. **What should happen next?** A policy recommendation and an accountable
   analyst workflow.

**Success criteria** are held-out fraud detection quality, false-alert burden,
measured inference latency and analyst task completion on synthetic scenarios
— not a promised accuracy number.

## 2. Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js App Router, TypeScript strict, Tailwind | Server rendering for a public homepage; typed client app |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic | Thin routes, typed contracts, migrations |
| Intelligence | pandas, NumPy, scikit-learn, XGBoost, SHAP, NetworkX | Tabular ML, anomaly detection, attribution, graph motifs |
| Database | PostgreSQL (Supabase managed, or Render Postgres) | Durable state, transactions, constraints |
| Auth | Supabase Auth, JWKS-verified server-side | No privileged credentials in the browser |
| LLM | Gemini via backend only, optional | Narrative only; never decides |
| Delivery | Two Docker web services on Render, Compose locally, GitHub Actions CI | Matches the plan's deployment target |

**Explicitly rejected:** microservices, an orchestration framework, a
multi-agent runtime, and any abstraction with a single trivial use.

## 3. Request flow

```text
validated transaction
  → chronological feature snapshot   (events strictly before `as_of`)
  → ML score + anomaly percentile
  → graph / agent / scam evidence
  → deterministic policy routing      (versioned thresholds)
  → persisted assessment + evidence
  → stored alert
  → analyst case
  → reviewed simulated action + audit event
  → optional generated narrative       (never authoritative)
```

## 4. Module boundaries

```text
backend/app/
  main.py            app factory, lifespan, router mounting
  api/v1/            thin HTTP routes — validate, delegate, serialise
  schemas/           Pydantic request/response contracts
  core/              settings, security, logging, error taxonomy
  models/            SQLAlchemy ORM tables
  repositories/      SQL lives here and nowhere else
  services/          business decisions and orchestration
  intelligence/      online features, inference, evidence, policy
```

Rules:

- HTTP routes stay thin; they never contain business decisions.
- Business decisions live in `services/`; they never contain raw SQL.
- Database operations live in `repositories/`.
- Inference is separate from training. Training never runs at request time or
  at application startup.

## 5. Data model (outline)

`entities`, `devices`, `transactions`, `login_events`, `assessments`,
`evidence`, `alerts`, `cases`, `case_events`, `audit_events`,
`simulation_runs`, `model_versions`.

Key invariants:

- Money is **integer poisha** end to end.
- Timestamps are UTC in storage, rendered in `Asia/Dhaka`.
- Indexes on transaction timestamp, sender/time, receiver/time, alert
  status/severity/time, case ownership.
- Synthetic truth labels live only in offline evaluation data / a separately
  controlled truth table. **Labels are never available to scoring features.**

## 6. Causal feature contract

A single versioned feature schema is shared by training and inference.
`feature_schema_version` is stamped on every model artifact and every
assessment. Readiness fails if they disagree.

Every window uses events **strictly preceding** the scored transaction, with
deterministic tie-breaking on equal timestamps. Features are computed *before*
the current event is appended to historical aggregates. Forbidden inputs:
final transaction resolution, future transactions, fraud labels, later analyst
decisions.

Feature groups: amount/type/channel/local-hour; prior-only sender 30-day
mean/median/std; rolling counts and sums at 5m/10m/1h/24h; recipient novelty;
device novelty and age; failed-login counts; location deviation and travel
evidence; recipient account age and distinct senders; pass-through ratio;
agent historical and peer-group deviation with minimum-sample rules.

Cold-start users use documented cohort baselines plus an explicit
`insufficient_history` flag — never an invented personal baseline.

## 7. Risk components are kept separate

Component scores are **not** averaged into a fake "fraud probability".
Isolation Forest output is an **anomaly percentile**, not a probability.
XGBoost output is a **model score** unless calibration is validated on
reserved data, in which case it may be labelled a probability.

Policy routing is deterministic and versioned:

| Level | Evidence | Suggested workflow |
|---|---|---|
| Low | No policy trigger, low model score | Allow; record assessment |
| Medium | One strong or several modest concerns | Simulated step-up verification / analyst review |
| High | Strong validated score or corroborated multi-source evidence | Simulated hold and urgent review |
| Insufficient / degraded | Missing data or model unavailable | Report uncertainty explicitly; documented fallback |

Thresholds come from validation under a documented review budget — not
arbitrary 0.5/0.8 defaults.

## 8. Explainability

Top signed feature contributions with observed vs historical values. SHAP
output units (log-odds for the chosen tree explainer) are stated explicitly.
Attribution values are **never** rescaled and displayed as a percentage fraud
probability.

Model attribution, policy rules, graph evidence and generated narrative are
presented as distinct sources. Stable evidence IDs let an analyst trace any
claim back to its origin.

## 9. Safety boundaries

- All hold/release/verify/block actions are **simulated only** and require an
  authorized analyst, a rationale, and produce an audit event.
- The LLM has no browser, shell, payment or admin tools. Transaction text and
  document content are treated as untrusted data that cannot override
  instructions.
- Backend verifies identity and role on every protected operation and checks
  case/run ownership. CORS is not authentication.
- No runtime SQLite or file-JSON storage for deployed state. No user-supplied
  model uploads. No pickle loading from untrusted sources.
