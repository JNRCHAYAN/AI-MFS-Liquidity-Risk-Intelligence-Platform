# upay Shield — Track 01: Trust & Risk Intelligence
## Complete agent build instructions, engineering plan, UI specification and delivery gates

Prepared: 2 October 2026. Product name is a proposed hackathon concept, not an official upay product or partnership claim.

## 1. Instructions to the coding agent

Build a working, professional, responsive Trust & Risk Intelligence prototype following this document. Implement one stage at a time, validate it, update documentation, commit it and push it before proceeding. Deliver actual integrated functionality; do not substitute decorative dashboards, hardcoded scores, dead buttons or fabricated metrics.

Use a modular monolith, one FastAPI service, one Next.js application and PostgreSQL. No multi-agent runtime is required. Gemini is an optional explanation service, never the authority deciding fraud or moving money. Prefer XGBoost as the initial classifier; LightGBM is an alternative experiment, not a second required model.

Before changing an existing repository, inspect README.md, AGENTS.md, Git status and existing architecture. Preserve unrelated work. If an applicable UI/design skill is installed, read it before UI implementation; never pretend a missing skill exists. Do not invoke a website hosting skill that changes the user's requested Render deployment provider.

Proceed autonomously within the authorized build scope. Never invent a GitHub remote, credentials, live URL, official deadline or successful test result. If a credential or remote is missing, continue independent local work and clearly record the blocked push/deployment. Do not claim completion until required checks and integrations pass.

At the end of every stage, report: implemented behavior; validation performed; relevant remaining limitation; commit SHA; pushed branch; next stage. Maintain `docs/PROGRESS.md` so another agent can resume.

## 2. Official sources and contest compliance

Read these supplied files before coding and keep a requirements traceability table:

1. `AI_Hackathon_2026_DIU_CPC_x_upay_Student_Guideline.md`, especially sections 3, 10–15.
2. `AI_Hackathon_2026_DIU_CPC_x_upay_Student_Guideline(1).md` — identical text to the first copy when this plan was prepared.
3. `AI_DEV_FEST_2026_AI_Hackathon_Rulebook.pdf`, sections 1–9.
4. `AI_DEV_FEST_2026_General_Rules.pdf`, sections 1–11.

| Requirement | Implementation/evidence |
|---|---|
| Teams have 1–3 registered members; own devices required | Record registered team and roles; bring institutional IDs and backup internet |
| Exactly 72 hours from official requirements publication | Record organizer-provided T+0 and deadline, with timezone; do not infer it from event date |
| On-site final on 7 October 2026; new requirements assigned | Reserve modular extension points; maintain an on-site change log |
| Final 90 minutes reserved for second evaluation | Finish on-site implementation and pushes before the announced implementation cutoff |
| Challenge-specific solution developed during official periods | Do not submit a substantially completed pre-contest challenge solution; retain truthful timestamps and development provenance |
| Public GitHub repository and continuous history | Commit and push every completed feature and meaningful fix; no single final dump |
| README sufficient to set up, run and test | Include all items in section 19 below |
| Initial video, report, repository and required materials | Prepare and submit through official channel before deadline |
| AI tools are permitted; use own accounts | Log significant tools/models and retain relevant prompt/development history |
| No external human assistance during active competition or sharing with other teams | Work only with registered teammates and permitted AI/resources; do not seek outside-human implementation help |
| Original work and disclosure | Attribute libraries, datasets, APIs and pre-existing components honestly |
| Synthetic/public/self-generated data, no real PII | Dataset card and clearly visible synthetic labels |
| Explainability, fairness, security, human oversight | Model card, reason evidence, evaluation slices, permission checks and audit history |
| Follow organizer clarifications | Record clarifications and update traceability; officially announced competition-specific instructions take precedence over conflicting general rules |

The guideline's evaluation weights are relevance 20%, AI/ML depth 20%, impact 20%, prototype 15%, innovation 10%, scalability/integration 10%, responsible AI/security 5%. Use these for preparation, not as a claim that final two-stage score allocation has been announced: the rulebook says detailed weighting will be announced by organizers.

## 3. Product definition and success criteria

**Problem statement:** For MFS fraud analysts, fragmented transaction and behavior signals make suspicious activity difficult to prioritize and investigate. upay Shield combines tabular ML, behavioral anomaly scores, transaction graph evidence and explicit policy rules to explain alerts and recommend review actions. Success is measured by held-out fraud detection quality, false-alert burden, measured inference latency and analyst task completion on synthetic scenarios.

**Primary user:** fraud analyst. Secondary: risk manager and hackathon judge. Customers, merchants and agents are simulated entities, not real account holders.

Every alert must answer:

1. What happened? Transaction, timeline, involved entities and behavior changes.
2. Why is it risky? Model attribution, anomaly evidence, graph motifs and rules with provenance.
3. What should happen next? A policy recommendation and an accountable analyst workflow.

### Complete Track 01 coverage

| Direction | Required implementation | Definition of done |
|---|---|---|
| Real-time transaction risk | XGBoost classifier, versioned feature engine, policy routing | New transaction receives persisted assessment with model version and evidence |
| Behavioral anomalies | Isolation Forest with historical deviation features | Unusual activity is ranked; anomaly score is not called fraud probability |
| Account takeover | Device/location/time/recipient/velocity evidence | ATO hypothesis includes observed evidence and innocent alternative explanations |
| Money mule/network risk | Time-bounded directed transaction graph and motifs | Analyst can inspect rapid pass-through, fan-in/fan-out and circular paths |
| Agent risk | Historical and peer-group robust comparisons | Flag unusual cash-in/out patterns relative to comparable synthetic agents |
| Scam intelligence | Scenario-specific transaction sequence heuristics | Evidence-backed scam hypothesis; no claim of knowing customer intent |
| Investigation assistant | Structured evidence-grounded summary, optional Gemini | Cites evidence IDs, respects permissions and cannot execute actions |

MVP includes all seven directions, but agent/scam/ATO start as transparent evidence rules rather than separately trained classifiers. Train only the core classifier and anomaly detector initially. Add advanced models only if time remains and validation justifies them.

### Acceptance goals, not promised results

- Compare ML against an explicit simple rules baseline on untouched temporal test data.
- Select alert thresholds on validation data under a documented review budget (e.g. 20 alerts per 1,000 transactions); report actual results, even if weak.
- Measure fraud precision, recall, average precision, false-positive rate and confusion matrix at chosen operating point.
- Target warm p95 scoring under 500 ms on the selected deployment hardware, excluding LLM generation; report actual measurements and hardware.
- Demonstrate all seeded scenarios and at least three benign confounders without hardcoding predicted outcomes.
- Zero real PII or secrets in repository; zero public access to privileged mutation APIs.
- Complete keyboard-accessible core flows at widths 360, 390, 768, 1024 and 1440 px without page-level horizontal overflow.

## 4. Architecture and stack

- Frontend: Next.js App Router, TypeScript strict mode, Tailwind CSS, accessible component primitives, TanStack Query, React Hook Form + Zod, Recharts and React Flow.
- Backend: Python 3.11 or 3.12, FastAPI, Pydantic settings, SQLAlchemy and Alembic.
- Intelligence: pandas, NumPy, scikit-learn, XGBoost, SHAP, NetworkX.
- Database: PostgreSQL; choose Supabase PostgreSQL as default managed datastore, or Render Postgres if explicitly selected. Do not implement both providers as separate systems.
- Authentication: Supabase Auth by default; backend validates signed tokens using supported issuer/audience/JWKS verification. Database service keys stay server-side.
- LLM: Gemini via backend only; configurable supported model identifier, optional API key.
- Tooling: pytest, Ruff, a type checker, ESLint, frontend typecheck and Playwright; lock dependency versions after resolving compatible releases.
- Delivery: two Docker web services on Render, local Docker Compose and GitHub Actions CI.

Flow: validated transaction → chronological feature snapshot → fraud/anomaly/network/agent/scam evidence → policy recommendation → stored alert → analyst case → reviewed action/audit → optional generated narrative.

Keep HTTP routes thin, business decisions in services, database operations in repositories and intelligence inference separate from training. Use explicit typed interfaces and dependency injection where it makes tests and replacement straightforward. Avoid unnecessary microservices, orchestration frameworks and abstractions with only one trivial use.

## 5. Repository layout and engineering rules

```text
upay-shield/
  README.md
  AGENTS.md
  .env.example
  .gitignore
  .dockerignore
  compose.yaml
  render.yaml
  .github/workflows/ci.yml
  frontend/
    Dockerfile
    package.json
    package-lock.json
    src/app/                     # public pages and authenticated app routes
    src/components/{ui,layout,charts,graph,forms}/
    src/features/{transactions,alerts,cases,simulation,models}/
    src/lib/{api,auth,formatting}/
    tests/
  backend/
    Dockerfile
    pyproject.toml
    dependency lock file
    alembic.ini
    migrations/
    app/
      main.py
      api/v1/
      schemas/
      core/                       # settings, security, logging, errors
      models/
      repositories/
      services/
      intelligence/               # online features, inference, evidence, policy
    tests/{unit,integration}/
  ml/
    generate_data.py
    build_features.py
    train_fraud.py
    train_anomaly.py
    evaluate.py
    calibrate.py
    package_artifacts.py
    artifacts/                    # small verified model bundle, not private raw data
  data/{samples,manifests}/
  contracts/openapi.json
  docs/
    PROGRESS.md
    architecture.md
    requirements-traceability.md
    data-card.md
    model-card.md
    evaluation.md
    threat-model.md
    ai-disclosure.md
    deployment-render.md
    demo-script.md
    project-report.md
    onsite-changes.md
```

- Keep a single authoritative feature schema shared by training and inference. Generate frontend API types from OpenAPI instead of maintaining divergent DTOs.
- Store money as integer poisha; display BDT/৳ using locale-aware formatting. Do not use binary floats for ledger quantities.
- Store timestamps in UTC; render Asia/Dhaka time with visible timezone. Derive behavioral hour/day in Asia/Dhaka consistently.
- Validate IDs, positive amounts, enums, timestamp ordering and bounds. Reject malformed inputs with actionable messages.
- Pagination, bounded graph queries and stable sorting are mandatory. Avoid fetching every transaction to calculate UI statistics.
- Use transactions and uniqueness constraints for deduplication. Handle duplicate IDs and idempotency keys safely.
- Log request ID, assessment ID, model version, duration and error category without token/secret leakage.
- No silent broad exception handlers, untyped arbitrary payloads, fabricated fallback success or speculative TODO-driven features.
- `.env.example` contains placeholders only; ignore secrets, virtual environments, node_modules, raw bulk data and generated build caches.
- Capture migration steps and meaningful decisions in docs. Verify dependencies rather than assuming remembered package APIs.

## 6. Data model and simulator

### Core tables

| Table | Important fields |
|---|---|
| entities | entity_id, kind(customer/agent/merchant), created_at, synthetic region, peer_group |
| devices | device_id, entity_id, first_seen_at, channel |
| transactions | id, sender_id, receiver_id, amount_poisha, type, timestamp, device_id, synthetic location, status, scenario_run_id |
| login_events | entity_id, timestamp, device_id, success, synthetic location |
| assessments | transaction_id, feature_snapshot, schema_version, raw_model_score, calibrated_probability(nullable), anomaly_percentile, policy_level, recommendation, model_version, policy_version, assessed_at |
| evidence | id, assessment_id, source, code, observed_value, baseline_value, reason_text, as_of, provenance |
| alerts | id, assessment_id, category, severity, status, assigned_to, created_at |
| cases | id, alert_id, owner, status, analyst_disposition, resolution_note, revision |
| case_events | id, case_id, actor, event_type, timestamp, metadata |
| audit_events | id, actor, action, object_id, request_id, timestamp, before/after metadata |
| simulation_runs | id, seed, scenario, simulated_clock, status, created_by |
| model_versions | id, artifact_checksum, dataset_manifest, metrics, feature_schema_version, trained_at |

Use indexes on transaction timestamp, sender/time, receiver/time, alert status/severity/time and case ownership. All synthetic truth labels belong in offline evaluation data or a separately controlled simulation truth table; never expose labels to scoring feature calculations.

### Simulator specification

Generate reproducible, chronological events for roughly 1,000 wallets, 50 merchants, 30 agents and 50,000–100,000 transactions, adjustable downward for resource limits. These are demo design choices, not official dataset requirements. Define realistic per-entity activity windows, varied amounts, repeat recipients, agent peer groups and benign travel/device replacement.

Implement scenarios:

1. Normal routine payment/cash-out.
2. ATO: failed logins → unseen device → new recipient → atypical large payment.
3. Velocity burst: multiple small transfers before a larger attempt.
4. Mule fan-in followed by quick pass-through/cash-out.
5. Circular transfer within a bounded time window.
6. Agent cash-out spike against history and comparable peers.
7. Scam pattern: new beneficiary + repeated escalation or split transfers under synthetic social-engineering context.
8. Benign confounders: salary-day spike, legitimate bulk merchant receipts, customer travel/new device with normal spending.

Allow overlapping normal/fraud distributions, multiple fraud families, subtle fraud and benign high-value transactions. Do not generate every fraud label from the same rules used as the baseline. Keep scenario truth out of inference requests. Document that synthetic validation demonstrates simulator performance, not real-bank fraud effectiveness.

Simulation controls must start, pause, step and reset a **run**, scoped by run ID; reset never wipes all database records. Store progress durably. Prefer bounded server-side steps triggered by UI requests over a fragile in-memory background loop for MVP. Poll stream results every 2–5 seconds with backoff; stop polling on hidden tabs and show last update time. This is near-real-time demo playback, not a claimed production event bus.

## 7. Feature engineering and ML pipeline

### Feature contract

Each feature has name, type, units, default/missing strategy, computation window and availability timestamp. Example set:

- Amount, transaction type, channel, local hour/day; cyclical hour features if helpful.
- Prior-only sender mean/median/std amount over 30 days; current amount ratio and robust deviation.
- Counts and sums over previous 5 minutes, 10 minutes, 1 hour and 24 hours.
- Recipient novelty; device novelty and time since first seen.
- Failed login count in previous hour; time since preceding login/transaction.
- Distance from historical synthetic location; missing-location flag and time-aware travel evidence.
- Recipient account age and historical distinct senders.
- Prior incoming/outgoing counts and amounts, short-window pass-through ratio.
- Agent historical and peer-group deviation, with minimum sample rules.

All windows must use events strictly preceding the scored transaction, with deterministic tie-breaking for equal timestamps. Compute features before appending current event to historical aggregates. Never use final transaction resolution, future transactions, fraud labels or later analyst decisions as current evidence.

ATO location changes alone are insufficient. Cold-start users use documented cohort baselines and expose insufficient-history flags instead of invented personal baselines. Do not use arbitrary wallet/device IDs as continuous features. Encode categories with persisted mappings or a supported fitted preprocessing pipeline; unseen categories must have a stable fallback.

### Training sequence

1. Generate data and manifest: seed, time range, class mix, fraud families and generator version.
2. Split chronologically into approximately 60% training, 15% tuning validation, 10% calibration/operating-point validation and 15% final test. Allow warm-up history; no tuning on test. Report class counts for each split.
3. Build causal snapshots using the same feature logic as the API. Prior historical context across boundaries is allowed; future outcomes are not.
4. Fit preprocessing on training only.
5. Train XGBoost binary classifier with conservative tree depth, regularization and early stopping against tuning validation. Calculate imbalance weight from training only; compare weighted/unweighted options using validation.
6. Train Isolation Forest on training-period nominal activity; state any label assumptions. Transform scores to empirical anomaly percentiles using separate reference data. Percentiles are not fraud probabilities.
7. Evaluate a simple deterministic baseline alongside ML. Tune thresholds on validation to satisfy a stated review budget or precision target.
8. If displaying probability, validate calibration on reserved data using reliability plots, Brier score and log loss. Fit sigmoid/isotonic calibration only if supported by sample size. Otherwise label output **model score**, not probability.
9. Freeze feature schema, threshold policy, model bundle and checksums before evaluating final test once.
10. Save actual test metrics, model card and artifact manifest; record package versions and data hash.

Metrics: average precision (state explicitly if used rather than trapezoidal PR-AUC), ROC-AUC, fraud precision/recall/F1, confusion matrix, false-positive rate, alert rate, recall at fixed review capacity, and synthetic fraud amount captured. Compare ML vs baseline and combined system vs ML-only. Report scenario-level performance and slice sizes by region, channel, amount bands and agent/customer category. Small slices must be marked inconclusive; do not claim fairness established from synthetic data.

Include a time/seed-shifted stress set or held-out fraud-family experiment if feasible, clearly separate from primary test and never use it for thresholds after claiming it is untouched.

### Artifacts and inference

Prefer XGBoost's supported native model format with JSON metadata. Serialized scikit-learn preprocessing/anomaly artifacts must be loaded only from your own trusted bundle; never accept model uploads from public users. Store checksum, ordered features, dtypes, library versions, thresholds and calibration metadata. Embed small artifacts in backend Docker image or retrieve from a pinned verified artifact source. Do not train on API requests or application startup.

Health readiness must fail if required artifacts/schema/checksum are invalid. Return explicit unavailable/degraded errors instead of inventing scores. Load once per process; cache explainer; enforce bounded explanation work.

### Explainability

Produce top signed feature contributions and observed vs historical values. State SHAP output units (typically log-odds for the chosen tree explainer configuration); never display `+23% fraud probability` by normalizing attribution values. Separate model attribution, policy rules, graph evidence and generated narrative. Stable evidence IDs let users inspect the source of each claim.

## 8. Supporting risk modules and policy

### Graph module

Maintain a time-bounded directed graph with transaction timestamps and amounts, only as-of the assessment. Detect bounded fan-in/fan-out, fast pass-through and short cycles. A recipient receiving many payments is not automatically a mule; compare merchant/agent context and legitimate flow. Return motif evidence with involved IDs and times, not a definitive criminal label.

Limit neighborhood depth to 1–2, result size initially to 100 nodes/300 edges, and graph computation to a configured time budget. Document truncated results. Cache by run/time bucket when safe. Never include future edges in historical risk scoring.

### Agent module

Use peer groups such as region + activity band + agent age. Compare cash-out share, transaction volume, short-window bursts, recipient concentration and reversals against prior medians/MAD. Require adequate peer history; emit insufficient evidence when absent. Explain the denominator and period.

### Scam module

Model **suspected scam pattern**, not customer intent. Use new-beneficiary escalation, rapid repeat transfers and prior recipient patterns as bounded heuristics. Optional synthetic customer-report text may enrich a case after scoring but is not an oracle available before transaction time. If scam text classification is added later, treat it as a separate validated task.

### Risk policy

Keep component scores separate. Do not average unrelated uncalibrated scores and call the result fraud probability. Define documented deterministic routing with versioned thresholds and reason codes:

| Level | Evidence | Suggested workflow |
|---|---|---|
| Low | No policy trigger and low model score | Allow normal simulated flow; record assessment |
| Medium | One strong concern or multiple modest concerns | Recommend simulated step-up verification or analyst review |
| High | Strong validated classifier score or corroborated multi-source evidence | Recommend simulated hold and urgent analyst review |
| Insufficient/degraded | Missing required data/model unavailable | Explicitly report uncertainty; follow documented review fallback |

Actual threshold numbers come from validation, not arbitrary 0.5/0.8 defaults. Optional combined **policy priority score** is allowed only if labeled as a policy ranking, with explicit formula and no probability claim.

All hold/release/verify/block buttons operate only in the synthetic simulation and require authorized analyst confirmation, rationale and audit logging. Do not connect to real money movement, lending decisions or upay production APIs.

## 9. Investigation assistant

Input: permission-scoped assessment, timeline, evidence records, component outputs and a small approved local policy document set. Implement a deterministic narrative first so the whole demo works without Gemini.

Gemini enhancement:

- Use supported SDK and configured model ID, key server-side, strict timeout, limited retries and budget.
- Require structured output: summary, observations with evidence IDs, uncertainty, suggested next steps and policy references.
- Treat transaction descriptions and document content as untrusted data; they cannot override system instructions or authorize actions.
- Validate evidence IDs exist in the authorized input. Reject unsupported claims and fall back to deterministic summary.
- Label generated text; show source evidence and policy version. Never manufacture a numeric confidence value.
- No browser, shell, payment or administrative tools available to the LLM.
- Cache by assessment ID + evidence revision + prompt/model version; record generation status.
- Chat requests must remain tied to an accessible case. Requesting another tenant/user's case must fail.

RAG is optional after structured summaries work. If added, retrieve only approved policy documents, cite section IDs and expose retrieved text; do not call arbitrary web content operational policy.

## 10. API contract

Prefix `/api/v1`; generate OpenAPI and frontend types. Provide typed errors, request IDs and pagination. Protect writes; public demo reads operate on immutable seed data.

| Method/path | Purpose |
|---|---|
| GET `/health/live` | Process alive; lightweight |
| GET `/health/ready` | Required database/model bundle available |
| GET `/api/v1/dashboard` | Filtered, server-aggregated KPIs/charts |
| GET `/api/v1/transactions` | Paginated/filterable transactions |
| POST `/api/v1/transactions/score` | Validate, causal features, score and persist idempotently |
| GET `/api/v1/transactions/{id}` | Transaction with permission-scoped assessment |
| GET `/api/v1/alerts` | Alert queue/filter/sort |
| PATCH `/api/v1/alerts/{id}` | Analyst assignment/status with audit |
| POST `/api/v1/cases` | Create case from accessible alert |
| GET `/api/v1/cases/{id}` | Case evidence and timeline |
| POST `/api/v1/cases/{id}/actions` | Confirmed simulated action with reason and revision |
| POST `/api/v1/cases/{id}/explanation` | Evidence-grounded summary generation |
| GET `/api/v1/network` | Bounded as-of neighborhood |
| GET `/api/v1/agents/{id}/risk` | Agent deviation and peer evidence |
| GET `/api/v1/models/current` | Version, manifest and genuine evaluation |
| POST `/api/v1/simulation/runs` | Analyst/admin creates scoped synthetic run |
| POST `/api/v1/simulation/runs/{id}/step` | Bounded idempotent advance |
| POST `/api/v1/simulation/runs/{id}/pause` | Pause run |
| POST `/api/v1/simulation/runs/{id}/reset` | Reset owned run with confirmation/audit |

Scoring response fields: assessment_id, transaction_id, assessed_at, as_of, model_version, feature_schema_version, raw_model_score, calibrated_probability(nullable), anomaly_percentile, category_hypotheses, policy_level, recommended_action, evidence[], limitations[], processing_ms. No synthetic truth label in ordinary analyst scoring responses.

## 11. Professional responsive UI/UX specification

### Visual direction

Build a calm fintech analyst workspace. Proposed tokens: navy `#0F172A`, teal `#0F766E`, neutral background `#F8FAFC`, white surfaces, muted text `#475569`; risk colors red/amber/green paired with labels/icons. These are proposed product colors, not asserted official upay branding. Verify contrast; use a readable font with suitable Bangla glyph support if bilingual text is added.

Use 8 px spacing rhythm, 12–16 px card radius, subtle borders, restrained shadows, readable 14–16 px body text and consistent numeric alignment. Avoid excessive gradients, stock neon AI styling, tiny labels and decorative charts with no analytical meaning. Light mode first; dark mode only after core functionality is complete.

### Public homepage `/`

1. Header: original text/logo, navigation to Features, How it works, Responsible AI and Demo; responsive menu.
2. Hero: “Understand risk. Protect trust.” Supporting description accurately explains synthetic fraud intelligence. Primary CTA “Explore demo”; secondary “How it works.”
3. Product preview using an actual screenshot or rendered demo data, explicitly labeled synthetic. Never fake a customer count, success rate or official endorsement.
4. Seven feature cards aligned with Track 01; each opens relevant demo/page or clear explanation.
5. Three-step flow: observe activity, explain risk, review action.
6. Evidence and transparency section: validated model metrics only after available, dataset scope and human review.
7. Responsible AI section: synthetic data, explainability, uncertainty and analyst oversight.
8. CTA and footer: repository link, documentation, team attribution and “Hackathon prototype; no real transactions.”

Homepage should load without authentication and remain usable when backend is unavailable. Render static product copy during build; do not require live API availability to build Next.js.

### Application routes

| Route | UX and behavior |
|---|---|
| `/app/overview` | KPIs: scored transactions, open alerts, alert rate, reviewed cases; trends and prioritized alerts; each metric has time range/definition |
| `/app/transactions` | Search by ID, date/type/risk filters, paginated table and details panel |
| `/app/transactions/[id]` | Amount, entities, assessment, evidence, component scores, explanation and create-case action |
| `/app/alerts` | Prioritized queue, assignments, category filters and review action |
| `/app/cases/[id]` | Evidence timeline, analyst notes, grounded summary, confirmed simulated actions and audit history |
| `/app/network` | Accessible graph plus equivalent evidence list/table, legend and bounded filters |
| `/app/agents` | Risk-ranked synthetic agents, peer comparisons and sample-size warnings |
| `/app/simulation` | Scenario selector, run controls, clock, reproducible seed and scenario truth toggle restricted to demo evaluation view |
| `/app/models` | Actual held-out results, baseline comparison, calibration, versions and limitations |
| `/app/settings` | Read-only policy defaults for analysts; permission-gated versioned edits only if implemented |

Shared shell: desktop collapsible sidebar, breadcrumb/title, date range, synthetic banner and account menu. Mobile: menu drawer, stacked cards, concise transaction cards, filter sheet and fullscreen detail pages. Use responsive chart heights and lazy-load graph code. Large tables may scroll inside a labeled region; page itself must not overflow.

### Mandatory states and accessibility

- Loading skeletons, useful empty states, API error with retry and unavailable/degraded banners.
- Preserve filters in URL query parameters; communicate stale data and offline state.
- Confirm risky simulated actions; prevent duplicate submission and show success/failure.
- Keyboard navigable menus/dialogs, visible focus, descriptive labels, focus restoration and reduced-motion support.
- Risk is never color-only. Charts have explanatory summaries; graph has list alternative.
- Touch targets generally at least 44 px. Avoid fixed widths preventing mobile use.
- No hidden clickable cards without semantic controls; no missing image alt text.
- Format money, dates and labels consistently. Never label flagged transaction value “money saved” or “blocked loss” without a clearly explained synthetic intervention calculation.

## 12. Authentication, safety and reliability

Public judges can explore a read-only demo without receiving a privileged password. Analyst sign-in enables scoped simulation/actions. Supply judge test access privately through the official method if needed; never commit privileged credentials in a public README.

Backend verifies identity and role for each protected operation and checks case/run ownership. Restrict allowed frontend origins; CORS is not authentication. Use rate limits for scoring, simulation and LLM endpoints, size limits, sanitized exports and bounded filters. Include permissions tests and prompt-injection scenarios in threat model.

If using Supabase directly from browser, enable appropriate RLS policies. Prefer backend mediation for transaction/case mutations. Configure least-privilege database credentials and appropriate TLS/pooling for managed PostgreSQL. Do not expose service role keys as `NEXT_PUBLIC_*` variables.

Use optimistic revisions for case changes, durable audit events and idempotency keys. No runtime SQLite/file JSON storage for deployed state. No user-controlled pickle loading. No raw stack traces or secrets in HTTP errors.

## 13. Git workflow: commit and push every completed feature

The user's request authorizes feature-by-feature pushes to the selected project repository. Configure only the remote actually supplied or verified for this project; do not reuse an unrelated repository from conversation history.

For a single agent, use the agreed working branch, normally `main` for a new dedicated repository. For registered teammates, use narrowly scoped feature branches, push each completed increment and merge through CI into main frequently without squashing away contest-required continuous history. Document folder ownership and interface changes to limit conflicts.

Before work: `git status`, `git remote -v`, `git branch --show-current`; fetch remote and reconcile baseline without discarding local edits. Never force-push or rewrite contest history.

After each feature:

1. Run relevant unit/integration/UI checks and formatting.
2. Update README, traceability and PROGRESS with feature status and actual checks.
3. Inspect `git diff` and staged files for secrets, accidental data and unrelated edits.
4. Stage specific intended paths, commit a meaningful Conventional Commit message.
5. Push current authorized branch; first push uses upstream tracking.
6. Verify push exit status and remote branch SHA matches local HEAD.
7. Record SHA and push result. Continue to next stage only after successful feature gate, or record an infrastructure blocker explicitly.

Example commands, after confirming branch and remote:

```bash
git add backend/app/intelligence backend/tests docs/PROGRESS.md
git diff --cached
git commit -m "feat(risk): score transactions with versioned fraud model"
git push origin HEAD
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Replace the final remote ref with the actual branch. Never blindly stage all files. If push is rejected, fetch and integrate without data loss; resolve conflicts, rerun affected checks and push again. Do not use force push as the fix. If authentication fails, preserve commits, record the failed push and request only missing access information while continuing local work.

CI on every push: backend lint/type/meaningful tests; frontend lint/typecheck/build; PostgreSQL integration tests; selected Playwright flows; container build checks for delivery changes. Render deployment may track main after CI succeeds; pushing a feature branch must not accidentally deploy half-integrated code.

## 14. Sequential implementation stages

Every stage ends with validated code, docs, a meaningful commit and a verified push. Split larger stages into multiple feature commits; do not defer all pushes until the end.

### Stage 0 — Contest scope and repository foundation

Create compliance/traceability, official-clock fields, architecture decisions and disclosure file. Set up public repo if already authorized and supported by available credentials, or document manual creation steps. Add AGENTS, README skeleton, ignore rules, dependency manifests and lockfiles. Do not invent release/deadline values.

Gate: source files referenced, repository runnable scaffold, no secrets. Commit: `chore: initialize track 01 project and contest documentation`.

### Stage 1 — Local infrastructure, database and contracts

Create FastAPI skeleton, Next.js skeleton, local Compose PostgreSQL, settings, migrations, health endpoints, API errors and OpenAPI generation. Define schemas before feature UI. Initialize authentication and role boundary early.

Gate: clean setup launches, migration works, health/readiness accurate, unauthorized mutation denied. Commit: `feat(platform): add database contracts and authenticated service shell`.

### Stage 2 — Simulator and causal features

Implement generator, manifests, seven scenarios and benign confounders, durable runs and shared chronological feature engine. Include sample-sized fixtures, not a giant raw dataset.

Gate: reproducible seed, correct money/time units, labels absent from inputs, feature-window correctness and run isolation. Commit: `feat(data): generate synthetic scenarios and causal risk features`.

### Stage 3 — Training, evaluation and artifact packaging

Train fraud classifier, Isolation Forest, baseline and optional calibration. Freeze validation policy; evaluate untouched test; package verified models and document genuine results.

Gate: reproduction command succeeds, feature parity verified, metrics generated from held-out data, artifacts load. Commit: `feat(ml): train and evaluate versioned fraud and anomaly models`.

### Stage 4 — Scoring, evidence and policy

Implement idempotent scoring, persisted assessments/evidence, explainability and policy recommendations. Make unavailable dependencies visible.

Gate: ordinary transaction and suspicious scenario scored via actual models; duplicate event safe; SHAP units correct; no future features. Commit: `feat(risk): integrate scoring explanations and review policy`.

### Stage 5 — ATO, network, agent and scam intelligence

Implement explicit evidence hypotheses, graph motifs and peer deviation. Keep all queries bounded and time-aware.

Gate: motif cases detected with evidence; benign merchant/travel scenarios assessed; no automatic criminal classification. Commit separately per completed module, e.g. `feat(network): detect time-bounded suspicious transfer motifs`.

### Stage 6 — Alerts, cases and audit workflow

Create alert queue, assignments, analyst dispositions, confirmed simulated actions and audit events. Add permission tests and optimistic concurrency.

Gate: analyst can open/review/resolve a case; read-only guest cannot mutate; updates durable after restart. Commit: `feat(cases): add analyst review and audited simulation actions`.

### Stage 7 — Investigation assistant

Implement deterministic summary, optional Gemini adapter, evidence validation, timeout fallback and safe policy retrieval if time allows.

Gate: key absent/API error still yields valid explanation; untrusted prompt cannot execute actions; summary references real evidence. Commit: `feat(copilot): add evidence-grounded investigation summaries`.

### Stage 8 — Homepage and responsive design system

Build tokens, common accessible components, homepage and app shell using section 11. Link CTAs to actual routes and clearly mark synthetic prototype.

Gate: homepage at all target widths, keyboard menu works, no fabricated endorsements/statistics. Commit: `feat(ui): build responsive homepage and analyst workspace shell`.

### Stage 9 — Integrated analyst screens

Build overview, transaction detail, alerts, cases, network, agents, simulator and model evaluation. Connect real APIs using generated types; handle all states.

Gate: Playwright exercises scenario → assessment → case → explanation → action; filter/pagination work; model page matches reports. Push each screen feature separately.

### Stage 10 — Render packaging and deployment

Complete Dockerfiles, blueprint/config docs, migrations, seeded demo and environment setup. Deploy actual services and validate access, restart persistence and fallbacks.

Gate: live public homepage + read-only demo, protected mutation APIs, readiness correct, database durable, deployed commit identified. Commit: `feat(deploy): package and verify Render deployment`.

### Stage 11 — Submission and on-site readiness

Finish README/report/demo script, record video, verify repository and files accessible, freeze initial tag and prepare on-site change log.

Gate: every submission component exists; all claims match actual product/metrics; final initial push inside official window. Commit: `docs: finalize submission evidence and judge setup guide`.

## 15. Time budget and team collaboration

The legal initial period is 72 hours from organizer T+0. If only 48 hours of development remain, prioritize the same integrated flow and reduce polish/advanced experiments, not integrity or required submission materials.

| Elapsed development time | Work |
|---|---|
| 0–6 h | Rules, repo, contracts, DB/auth and basic UI shell |
| 6–16 h | Simulator, features and baseline/model training |
| 16–26 h | Scoring, evidence, policy and remaining risk modules |
| 26–36 h | Case workflow, summaries, homepage and integrated screens |
| 36–42 h | Deploy, integration tests, responsive corrections |
| 42–48 h | Report/video/README and submission verification |
| Remaining official time if available | Better validation, accessibility, robustness and rehearsal |

For three registered teammates: member A owns `ml/`, data and intelligence; B owns backend/API/auth/deployment; C owns frontend/UI and demo materials. Agree OpenAPI/feature contract first. For two members, combine A+B with one person and C+report with the other. Do not let concurrent edits modify the same migrations/contracts without coordination; one owner integrates these shared files. Each member must understand the full submitted system.

Cut order when time is tight: dark mode, RAG/vector DB, sophisticated graph ML, streaming infrastructure, extra models and advanced animation. Keep all seven directions as working evidence-backed capabilities and document the depth honestly.

## 16. Verification strategy

Write meaningful tests around risk logic and integration, not tests that merely reproduce implementation.

- Causal windows: current/future events excluded, equal-time ordering stable, feature train/inference parity.
- Data: seed reproducibility, money boundaries, timezone derivation, missing histories and duplicate transaction IDs.
- Models: artifact checksum/schema mismatch detected; probability labels obey calibration availability; real test metrics and baseline generated.
- Graph: time-bounded motifs, future-edge exclusion, limits and legitimate merchant confounder.
- API: permissions, validation, idempotency, pagination, case revisions and audit persistence.
- Assistant: invalid evidence IDs, injected instructions, no API key, timeout and unauthorized case.
- UI: keyboard navigation, filter/sort, modal confirmation, error/empty/loading states and responsive breakpoints.
- End-to-end: start owned run → step seeded scenario → inspect actual alert → open case → generate summary → confirm simulated review → reload and inspect audit.
- Deployment: HTTP checks, HTTPS API URL, persistence after redeploy/restart, model readiness and known deployed SHA.

Provide commands through project scripts such as `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e`, `ruff check .`, `pytest`, and the actual configured Python typecheck command. Document prerequisites and expected outputs; do not claim scripts exist until implemented.

## 17. Render deployment design

Use Render for both frontend and backend. Local Compose is for local development; describe two separate deployed services in Render configuration rather than asking Render to run the Compose file.

### Services

1. `shield-api`: Docker web service, repository-root build context with backend Dockerfile; exposes FastAPI bound to `0.0.0.0` and Render-provided `PORT`. Single worker initially to control model memory; add workers only after measurement.
2. `shield-web`: Next.js Docker web service, appropriate build context and lockfile, standalone production output, bound to `0.0.0.0` and `PORT`.
3. External Supabase PostgreSQL/Auth, or the explicitly chosen Render PostgreSQL replacement.

Use non-root runtime images, pinned compatible dependencies, `.dockerignore`, multistage builds and no embedded secrets. Use exec-form startup where practical with a small entrypoint that expands `PORT` and forwards termination signals. Copy Next.js standalone output, static assets and public assets correctly for the selected layout.

Keep models in image or pinned verified artifact storage; Render's default service filesystem is ephemeral. Do not persist case state, simulator state, user uploads or model changes in local container files. Database is authoritative.

### Configuration contract

| Variable | Location | Purpose |
|---|---|---|
| `DATABASE_URL` | Backend secret | TLS/pooling-aware PostgreSQL connection |
| `SUPABASE_URL` | Backend / public auth client config | Project URL |
| `SUPABASE_JWT_ISSUER` | Backend | Expected token issuer |
| `SUPABASE_JWT_AUDIENCE` | Backend | Expected token audience |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend secret only, only if needed | Privileged server operation; never public |
| `GEMINI_API_KEY` | Backend secret, optional | Generated explanations |
| `GEMINI_MODEL` | Backend | Verified supported model name |
| `CORS_ORIGINS` | Backend | Exact frontend origin allowlist |
| `MODEL_BUNDLE_PATH` | Backend | Packaged model directory |
| `APP_ENV`, `LOG_LEVEL` | Backend | Runtime configuration |
| `DEMO_READ_ONLY` | Backend | Protect public seed demo |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend build configuration | HTTPS public API origin |
| `NEXT_PUBLIC_SUPABASE_URL` | Frontend build configuration | Public Auth project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Frontend build configuration | Public client key only, with appropriate access controls |
| `PORT` | Runtime provided by Render | Listening port; do not hardcode deployment port |

Public frontend variables are bundled at build time; changes require rebuild. Alternatively implement a documented same-origin server proxy using runtime API configuration, but choose one approach and keep contracts consistent.

### Deployment steps

1. Verify local containers and migrate local DB; package trusted model artifacts before backend build.
2. Push current tested source. Create/validate `render.yaml` against current official Blueprint schema; do not guess unsupported fields.
3. Connect correct public repository and main branch in Render; choose service plans appropriate to measured memory. Check current plan availability/limits rather than assuming a free always-on service.
4. Provision/configure datastore and auth; add secrets only in provider environment configuration.
5. Run production migrations once through a supported pre-deploy mechanism or documented controlled one-off command. Do not rely on multiple application workers racing to migrate.
6. Deploy API, set health check path `/health/ready`, confirm model and DB readiness.
7. Deploy frontend with actual API URL and auth public configuration. Set API CORS to exact frontend origin and configure auth redirect URLs.
8. Seed immutable synthetic demo idempotently; ensure guest can read it and cannot reset or alter it.
9. Run live smoke and end-to-end checks; document URLs and commit SHA in README.
10. Exercise restart/redeploy persistence and Gemini outage fallback. Keep a reproducible local demo backup for uncertain event internet.

Render automatic deployment should follow main only after the selected CI gates. Verify deployment status before calling it live; rollback by selecting a known-good prior source/deployment without rewriting Git history. Do not expose private environment values in screenshots.

Official references checked while preparing this plan:
- https://render.com/docs/docker
- https://render.com/docs/deploys
- https://render.com/docs/health-checks
- https://render.com/docs/blueprint-spec
- https://render.com/docs/web-services

## 18. Evidence, impact and demo

Report synthetic evaluation honestly. Track detected fraud count, false alerts per 1,000 transactions, review-capacity recall, median/p95 inference time, and case workflow duration. Synthetic flagged value is not real loss prevented. Any savings estimate requires explicit assumptions about successful intervention and fraud losses.

Suggested demo sequence (adjust duration to organizer instructions):

1. Explain analyst problem and show polished homepage.
2. Open synthetic dashboard and inspect a benign transaction.
3. Replay ATO/velocity scenario and inspect scored evidence.
4. Inspect mule graph path and agent/scam evidence.
5. Create case; show summary, uncertainty and analyst-confirmed simulated action.
6. Show held-out metrics vs rules baseline and responsible AI limitations.
7. Show deployment/reproducibility and continuous Git history.

Never force model scores to match the demo script. If a scenario is missed, show the actual result and its limitation or fix and rerun validation before submission.

## 19. Required README and submission files

README must include:

- Problem, users, purpose and proposed solution.
- Implemented features, distinguishing completed, limited and future work.
- How each AI component works and why it adds value beyond rules.
- Stack, models, APIs, libraries and external services.
- Software/hardware requirements and exact compatible versions.
- Installation, dependencies, database migration and synthetic seed commands.
- Environment variable names, purposes and placeholders.
- Exact local run, production build, Docker and training/evaluation commands.
- Actual live URLs and access instructions without privileged public credentials.
- Testing and demo verification commands.
- Auth redirects, CORS, artifacts, dataset assumptions and other required configuration.
- Actual metrics and limitations; synthetic scope and no production claims.
- Team members, attribution, dataset/API/model/component disclosure and AI tool use.
- Render deployment instructions and troubleshooting.

Project report: problem, idea, architecture, implemented features, dataset strategy, AI approach, methodology, actual evaluation, intended impact, responsibility/security, limitations and future validation.

Before deadline verify: public repository accessible; initial commits/pushes within official period; complete README; report file and video link accessible; prototype/project materials included; live app reachable; organizer submission format/channel satisfied. Do not infer required video length or report format when organizers have not announced it. Tag the initial submission, then maintain ordinary new commits for on-site updates.

## 20. On-site change plan and final completion checklist

Prepare modular policies, generated contracts, migration process and reproducible training scripts so new requirements can be integrated quickly. Record assigned changes, implemented behavior, checks and push SHAs in `docs/onsite-changes.md`. Push within on-site implementation window; reserve final 90 minutes for demonstration and questions.

- [ ] Official release time and deadline recorded accurately.
- [ ] All seven Track 01 directions implemented at documented depth.
- [ ] Actual XGBoost and anomaly inference; no canned fraud scores.
- [ ] Causal features and uncontaminated held-out test.
- [ ] Explanations use truthful attribution units and source evidence.
- [ ] Human review and simulated-only consequential actions.
- [ ] Homepage and all core analyst pages responsive and accessible.
- [ ] Auth, permissions, idempotency and audit workflow tested.
- [ ] Gemini optional; fallback fully works.
- [ ] Durable database state; model artifacts load on Render.
- [ ] Continuous commits and verified feature pushes.
- [ ] CI and live smoke checks pass, with actual URLs documented.
- [ ] Dataset/model/disclosure/security docs complete.
- [ ] README reproduces setup, run, training, testing and deployment.
- [ ] Video, report and official submission materials complete and accessible.
- [ ] Registered teammates can explain design, models, limitations and changes.

## Copy-paste kickoff prompt

> Build upay Shield following `UPAY_SHIELD_TRACK_01_AGENT_BUILD_PLAN.md`. First inspect the repository, AGENTS.md, supplied official rules and available relevant skills. Implement sequentially from Stage 0, with real causal features, trained models, evidence-backed risk modules, professional responsive homepage and analyst UI. Use Next.js/TypeScript/Tailwind, FastAPI/Python/PostgreSQL, XGBoost, Isolation Forest, SHAP, NetworkX and optional Gemini explanations. Use synthetic data only. Run the relevant validation for every feature, update README and PROGRESS, commit and push the completed increment to the verified authorized repository before proceeding. Never invent secrets, metrics, URLs or successful pushes. Deploy the two Docker services to Render with durable database state and verified readiness. Preserve continuous contest history, produce submission evidence and document limitations honestly. Start with repository/rules inspection and the first concrete implementation stage.
