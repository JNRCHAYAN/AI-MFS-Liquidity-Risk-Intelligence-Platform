# PROGRESS

Living status file. Another agent should be able to resume from this file
alone. Updated at the end of every stage.

Last updated: 2 October 2026.

## Official clock

| Field | Value |
|---|---|
| T+0 (requirements publication) | **NOT PROVIDED by organizer** |
| Initial submission deadline (T+72h) | **NOT PROVIDED by organizer** |
| Organizer timezone | **NOT PROVIDED** |

See `docs/requirements-traceability.md` §1.1 for the open §9.3 pre-contest
compliance risk.

## Environment — verified by running it

| Tool | Version | Verified how |
|---|---|---|
| Python | 3.14.8 | Plan specifies 3.11/3.12; see note below |
| Node | v24.21.0 | `npm run build` succeeds |
| npm | 11.19.0 | — |
| Docker | 29.8.1 | Daemon started; `docker info` returns a server version |
| PostgreSQL | 16-alpine | Compose service `shield-db` reached `healthy` |
| Git | 2.56.0 | — |

### Python version note — RESOLVED

Only Python 3.14.8 is installed, not the planned 3.11/3.12. This was tested
rather than assumed: the whole ML stack installs **and runs** on cp314.

| Package | Verified version | Runtime check performed |
|---|---|---|
| numpy | 2.5.3 | imported |
| pandas | 3.0.6 | imported — **pandas 3.x**, verify APIs, do not assume 2.x |
| scikit-learn | 1.9.1 | `IsolationForest.score_samples` executed |
| xgboost | 3.4.1 | `XGBClassifier.fit` / `predict_proba` executed |
| shap | 0.52.0 | imported (numba 0.68.0 / llvmlite 0.50.0 present) |
| networkx | 3.7 | imported |
| scipy | 1.18.1 | imported |
| fastapi | 0.142.2 | server starts and serves |
| starlette | 1.7.0 | **1.x** — `app.routes` internals differ from 0.x |
| uvicorn | 0.54.0 | serving |

No interpreter fallback is required.

## What actually runs today

| Component | State | Verification |
|---|---|---|
| PostgreSQL | Running | `shield-db` healthy; 14 tables, 58 indexes |
| Migrations | Applied | `alembic upgrade head` exit 0 against live PostgreSQL |
| Backend API | Running on :8000 | see endpoint results below |
| Frontend | Running on :3000 | `/` and `/app/overview` both HTTP 200 |

### Verified endpoint behaviour

| Request | Result |
|---|---|
| `GET /health/live` | 200 `{"status":"alive"}` |
| `GET /health/ready` | **503**, honestly reporting: `database ok`, `model_bundle unavailable` (training not run), `llm degraded` (optional) |
| `GET /api/v1/unknown` | 404 with a typed error envelope carrying a real request ID |

### Verified checks

| Check | Command | Result |
|---|---|---|
| Backend lint | `ruff check .` | All checks passed |
| Backend tests | `pytest` | **13 passed** |
| Migration SQL | `alembic upgrade head` | 14 tables, 58 indexes created |
| Frontend types | `npm run typecheck` | exit 0 |
| Frontend lint | `npm run lint` | exit 0 |
| Frontend build | `npm run build` | exit 0; `/` prerendered static |

## Stage status

| Stage | Description | Status |
|---|---|---|
| 0 | Contest scope and repository foundation | **Done** |
| 1 | Local infrastructure, database and contracts | **Mostly done** — auth/role boundary not yet implemented |
| 2 | Simulator and causal features | Simulator written; **feature engine not started** |
| 3 | Training, evaluation and artifact packaging | Not started |
| 4 | Scoring, evidence and policy | Not started |
| 5 | ATO, network, agent and scam intelligence | Not started |
| 6 | Alerts, cases and audit workflow | Not started |
| 7 | Investigation assistant | Not started |
| 8 | Homepage and responsive design system | Homepage done |
| 9 | Integrated analyst screens | Not started |
| 10 | Render packaging and deployment | Not started |
| 11 | Submission and on-site readiness | Not started |

## Commit history

| SHA | Message |
|---|---|
| `c6353e4` | chore: initialize track 01 project and contest documentation |
| `eda0bc0` | feat(platform): add frozen feature contract, settings and local infrastructure |
| `00788ec` | feat(data): add reproducible synthetic MFS transaction generator |
| `2550c9c` | feat(db): add PostgreSQL schema, migrations and repositories |
| `d4f80c9` | feat(api): add application shell, readiness probes and error handling |
| `5225dce` | feat(ui): add responsive homepage and analyst workspace shell |
| `702ceb9` | docs: add demo script and on-site change log |

All pushed to `origin/master`; local and remote SHAs verified equal.

## Bugs found and fixed by running the code

The previous subagent run reported the frontend as complete. Actually building
it revealed it had never been built. Real faults corrected:

1. `cta-footer.tsx` imported `Github` from lucide-react, which **removed brand
   icons in 1.x**. Replaced with a local inline SVG.
2. `next.config.ts` set an `eslint` key removed in Next 16.
3. Error envelopes returned `request_id: null` — handlers read the inbound
   header instead of the middleware-assigned ID.
4. `MODEL_BUNDLE_PATH` resolved against the working directory, so the same
   config pointed at different paths depending on where the API was started.
5. `pyproject.toml` `readme` referenced a path outside the build root, breaking
   both editable install and the Docker build.
6. A test's inherited-method allowlist was hard-coded and incomplete; it is now
   derived from `BaseRepository` so it cannot drift.

## Not yet verified — do not claim these

- **Simulator determinism.** The generator writes per-file sha256 hashes to its
  manifest, but the two-run comparison was interrupted. Unverified.
- **Feature train/inference parity.** The feature engine does not exist yet.
- **Any model metric.** No model has been trained.
- **Render deployment.** Nothing is deployed; no live URL exists.

## Known limitations

1. No authentication or role boundary yet — Stage 1's permission requirement
   is unmet.
2. `npm run start` does not work with `output: "standalone"`; the standalone
   server must be launched via `node .next/standalone/server.js`. The README's
   run instructions need correcting.
3. The app shell's `/app/overview` is an honest placeholder with no data.

## Next step

Stage 2/3: build the causal feature engine against
`FEATURE_SCHEMA_VERSION 1.0.0` and `TransactionRepository.events_before()`,
verify train/inference parity, then train and evaluate. In parallel, the
remaining risk, workflow and analyst-screen workstreams can proceed once the
feature contract is producing values.
