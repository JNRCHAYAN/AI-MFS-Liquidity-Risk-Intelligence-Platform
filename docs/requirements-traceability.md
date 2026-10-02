# Requirements Traceability — upay Shield (Track 01)

Prepared: 2 October 2026. Product name is a proposed hackathon concept, not an
official upay product or partnership claim.

This file maps every supplied official requirement to the implementation or
evidence that satisfies it. It is updated at each stage. Requirements marked
**OPEN** are not yet satisfied.

## 1. Official clock (organizer-provided values)

The rulebook states the initial development period is *exactly 72 hours from
publication of the problem requirements* (T+0), and that **the organizers
announce the exact release time, submission deadline, on-site start time and
update-implementation duration separately**.

| Field | Value | Source |
|---|---|---|
| T+0 (requirements publication) | **NOT PROVIDED by organizer** | To be announced separately |
| T+72h (initial submission deadline) | **NOT PROVIDED by organizer** | To be announced separately |
| Organizer timezone for deadlines | **NOT PROVIDED** | To be announced separately |
| On-site final date | 7 October 2026 | AI Hackathon Rulebook, p.1 |
| Event dates | 6–7 October 2026 | General Rules, p.1 |
| Second evaluation window | Final 90 minutes of the on-site contest | Rulebook §8.4 |
| On-site late-arrival allowance | Up to 1 hour after start, no extension | General Rules §3.2 |

> **Deliberate omission.** No T+0 timestamp is recorded here because none has
> been announced. It is NOT inferred from the event date, and no deadline is
> guessed. This complies with the build plan's instruction to never invent an
> official deadline.

### 1.1 Open compliance risk — pre-contest solution (Rulebook §9.3)

The build plan instructs that work proceed autonomously. The organizer has
**not yet published T+0**, therefore the project's position inside or outside
the official 72-hour development window is currently **unknown**.

| Rule | Requirement | Current status |
|---|---|---|
| §9.3 | Must not submit a substantially completed, challenge-specific solution prepared before the official development period | **OPEN — unresolved** |
| §5.2 | Continuous commit history throughout the initial development phase | Tracked in `docs/PROGRESS.md` |
| §5.5 | Initial code pushed by the initial submission deadline | Blocked: deadline not announced |

**Mitigation applied.** Every commit in this repository is timestamped by Git
and the development provenance is recorded truthfully in `docs/PROGRESS.md`
and `docs/ai-disclosure.md`. No commit date is backdated or altered. If the
organizer confirms T+0 falls after the start of this build, the correct
remedy is to disclose that plainly rather than misrepresent the timeline.

## 2. Team and registration

| Requirement | Source | Implementation / evidence |
|---|---|---|
| Teams of 1–3 members | Rulebook §2.1 | **OPEN** — registered roster and roles to be recorded below |
| All members officially registered; no substitutions | Rulebook §2.2 | **OPEN** — organizer-side requirement |
| Participants bring own devices | Rulebook §2.3; General Rules §2.1–2.2 | **OPEN** — operational; bring backup internet |
| Carry valid institutional ID | General Rules §1.2 | **OPEN** — operational |
| Physical presence for kit collection | General Rules §1.3 | **OPEN** — operational |

## 3. Development rules

| Requirement | Source | Implementation / evidence |
|---|---|---|
| Ideas and solution developed in the official period | Rulebook §4.1 | See §1.1 risk above |
| AI models, APIs, pretrained models, libraries, public datasets permitted | Rulebook §4.2 | `docs/ai-disclosure.md` |
| Pre-existing general-purpose components permitted, not misrepresented | Rulebook §4.3, §9.2 | `docs/ai-disclosure.md` |
| Disclose external datasets/APIs/services on request | Rulebook §4.4; General Rules §5.6 | `docs/ai-disclosure.md` |
| Every member can explain design, implementation, AI components | Rulebook §4.5, §9.4 | `docs/demo-script.md` |
| All data synthetic/public/self-generated; no real PII | Guideline §11, §14 | `docs/data-card.md` |
| No external human assistance during active competition | General Rules §4.1–4.2 | Operational |
| Own AI accounts only | General Rules §5.3 | Operational |

## 4. GitHub and development history

| Requirement | Source | Implementation / evidence |
|---|---|---|
| Public GitHub repository | Rulebook §5.1 | `origin` configured |
| Code committed and pushed within the contest period | Rulebook §5.1, §5.5 | Per-stage pushes, SHAs in `docs/PROGRESS.md` |
| Clear and continuous commit history | Rulebook §5.2 | Conventional Commits, one increment per commit |
| Step-by-step commits; no single final upload | Rulebook §5.3 | Enforced by stage-by-stage workflow |
| Source code, project files and complete README | Rulebook §5.4 | `README.md` |
| Never force-push or rewrite contest history | Build plan §13 | Operational |

## 5. Mandatory README.md (Rulebook §6.2)

Each item below must be present in `README.md`.

| Required item | Status |
|---|---|
| Project overview — problem, solution, purpose | **OPEN** |
| Features and how AI components are used | **OPEN** |
| Technology stack | **OPEN** |
| Requirements — software, dependencies, hardware | **OPEN** |
| Installation and setup instructions | **OPEN** |
| Environment variables with placeholders | **OPEN** — `.env.example` created |
| Run and build commands | **OPEN** |
| Live deployment URL | **OPEN** — no deployment yet |
| Testing instructions | **OPEN** |
| Other configuration | **OPEN** |

## 6. Submission requirements (Rulebook §7)

| Item | Source | Status |
|---|---|---|
| Video demonstration | Rulebook §7.1, §7.2 | **OPEN** — required format not announced |
| Project report file | Rulebook §7.1, §7.3 | **OPEN** — `docs/project-report.md` pending |
| Public GitHub repository link | Rulebook §7.1 | **OPEN** — not yet submitted |
| Required prototype / project files | Rulebook §7.4 | **OPEN** |
| Submission via official channel | Rulebook §7.4; General Rules §8.1 | **OPEN** — channel not announced |

> Video length, report format and file-format requirements have **not** been
> announced by the organizers and are therefore not assumed here.

## 7. Evaluation criteria (Guideline §15)

The guideline publishes these weights for preparation. Rulebook §8.5 states
the **detailed marking criteria, score allocation and weighting of the two
evaluations will be announced by the organizers** — so these are used as
design guidance, not as a claim about final scoring.

| Criterion | Weight | Design response |
|---|---|---|
| Problem relevance | 20% | `docs/architecture.md` §1 problem statement |
| AI/ML depth | 20% | XGBoost classifier, Isolation Forest, SHAP, graph analytics |
| Business/customer impact | 20% | `docs/evaluation.md` — measured on held-out synthetic data |
| Prototype quality | 15% | Working end-to-end FastAPI + Next.js prototype |
| Innovation | 10% | Multi-source evidence fusion with bounded, time-aware graphs |
| Scalability & integration | 10% | Versioned contracts, migrations, Render deployment |
| Responsible AI & security | 5% | `docs/model-card.md`, `docs/threat-model.md` |

## 8. Responsible AI requirements (Guideline §14)

| Principle | Implementation / evidence |
|---|---|
| Privacy — synthetic/public data only | `docs/data-card.md` |
| Explainability — show reasons for predictions | SHAP attributions + evidence records |
| Fairness — check behaviour across groups | Evaluation slices in `docs/evaluation.md` |
| Security — injection, leakage, access control | `docs/threat-model.md` |
| Human oversight | Analyst-confirmed, simulated-only actions |
| Transparency — separate prediction from explanation | Evidence provenance in API contract |
| No harmful automation | No autonomous consequential decisions |
