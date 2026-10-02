# Demo Script

Rulebook §7.2 requires the video to demonstrate how the implemented idea works,
explain the features and AI components implemented, and describe real-life
impact or practical value.

> **Duration is not fixed here.** The organizer has not announced the required
> video length (Rulebook §7.4 leaves format to the organizers). Adjust the
> timings below once it is announced.

## The three questions the demo must answer

A strong Track 01 project answers: **what happened?** — **why is it risky?** —
**what should upay do next?** Every segment below is built around those.

## Pre-flight checklist

- [ ] Backend running, `/health/ready` returns ready with a valid model bundle
- [ ] Frontend running or deployed and reachable
- [ ] A seeded synthetic simulation run exists
- [ ] Screen at 1440px; notifications silenced; no personal data on screen
- [ ] No secret, key or environment value visible in any recording frame

## Segment plan

| # | Segment | Shows | Why the judge cares |
|---|---|---|---|
| 1 | **Problem + homepage** (`/`) | The analyst problem; the public homepage; the synthetic-data notice | Problem relevance (20%) |
| 2 | **Benign transaction** | A normal transaction scored in the dashboard, with its assessment | The system does not cry wolf — false-alert burden matters |
| 3 | **ATO / velocity scenario** | Replay the scenario, open the scored transaction, read the evidence | AI/ML depth (20%) — real model, real causal features |
| 4 | **Mule network** | The bounded graph: fan-in, pass-through, cycle; then the **list alternative** | Innovation (10%) — and accessibility |
| 5 | **Agent + scam evidence** | Peer-relative agent deviation with sample-size warning; scam-pattern heuristic | Depth across all seven Track 01 directions |
| 6 | **Case workflow** | Create a case, generate the grounded summary, confirm a *simulated* action, show the audit entry | Prototype quality (15%), responsible AI (5%) |
| 7 | **Model evaluation** (`/app/models`) | Held-out metrics vs the rules baseline; calibration; limitations | Honest evidence, not an accuracy claim |
| 8 | **Reproducibility** | Git history, CI, deployment, README setup | Scalability & integration (10%) |

## Narration notes

**On honesty.** If a seeded scenario is *not* detected by the model, show the
actual result and explain the limitation. Never force a model score to match
this script. A demonstrated limitation explained well reads as engineering
maturity; a staged success discovered by a judge reads as fabrication.

**On language.** Say "model score" or "anomaly percentile" — never "fraud
probability" — unless calibration has been validated on reserved data.

**On the synthetic scope.** State plainly, more than once: this is synthetic
data. A high held-out metric demonstrates that the **simulator** produced a
learnable signal. It does **not** demonstrate real-bank fraud effectiveness,
and the demo must not imply that it does.

**On value.** Do not say money was "saved" or "blocked". Synthetic flagged
value is not real loss prevented. If an estimate is offered, state the
assumptions behind it explicitly.

**On the LLM.** If Gemini is unavailable during the demo, that is fine — show
the deterministic summary path. This is a feature, not a failure: the product
works without the LLM, and the LLM never makes the decision.

## Closing statement

Summarise: the seven Track 01 directions are implemented as working,
evidence-backed capabilities; the model is genuinely trained and evaluated on
untouched temporal test data; every consequential action is simulated and
human-approved; and the whole system is reproducible from the README.

## Backup plan

Keep a locally recorded run and a local Docker Compose demo as a fallback —
venue internet is not guaranteed (General Rules §2.2).
