# On-Site Change Log

Rulebook §8.3 requires that final-day updates be documented through the
ongoing Git commit history and pushed within the allotted on-site time.

**Status: no on-site phase has occurred yet.** The organizer has not announced
the on-site start time or the update-implementation duration (see
`docs/requirements-traceability.md` §1). This file is prepared so that changes
can be recorded immediately when they are received.

## Process

1. Record the assigned change verbatim, with the time it was received and the
   organizer-provided deadline.
2. Implement on a scoped branch or directly on the working branch, whichever
   the team agrees.
3. Run the affected checks and record the actual result.
4. Commit each change separately with a meaningful message.
5. Push within the on-site implementation window.
6. Record the commit SHA and push result below.
7. Reserve the final 90 minutes for the second evaluation — do not leave
   implementation running into the demonstration window.

## Prepared extension points

The architecture was built so new requirements can be integrated quickly:

| Extension point | Location |
|---|---|
| New feature | Add to `FEATURE_SCHEMA_VERSION` in `backend/app/intelligence/features/schema.py`, bump the version, retrain |
| New risk signal | Add a module under `backend/app/intelligence/risk_modules/` |
| New policy rule | Versioned thresholds in the policy module — no model retrain needed |
| New API route | `backend/app/api/v1/` — routes are thin, decisions live in services |
| New UI screen | `frontend/src/app/app/` using the existing design system |
| New table/column | Standard Alembic migration |

## Log

| Received (UTC) | Assigned change | Deadline | Implementation | Checks run | Commit SHA | Pushed |
|---|---|---|---|---|---|---|
| — | *No on-site requirements received yet* | — | — | — | — | — |
