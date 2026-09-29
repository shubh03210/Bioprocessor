# Implementation Plan

**Document ID:** `08-IMPLEMENTATION_PLAN`  
**Rule:** Follow phases in order. **DO NOT implement optional extensions (E1–E4) until all mandatory requirements are complete and tested.**

---

## Phase 0 — Project foundation

| | |
|--|--|
| **Objective** | Scaffold repo layout, tooling, README stubs already present, env templates |
| **Tasks** | Create `backend/`, `frontend/`, `simulator/` skeletons; dependency manifests; `.env.example`; wire scripts; copy/link `data_kit` |
| **Files/modules** | `backend/pyproject.toml` or `requirements.txt`; `frontend/package.json`; root scripts |
| **Dependencies** | Docs complete (this bootstrap) |
| **Acceptance** | Apps start empty health/hello without business logic required |
| **Tests** | Smoke: install + import |
| **DoD** | Contributors can clone and install |
| **Status** | DONE (2026-09-29) |

---

## Phase 1 — Database and migrations

| | |
|--|--|
| **Objective** | Implement schema from `04-DATABASE_DESIGN.md` |
| **Tasks** | SQLModel/SQLAlchemy models; Alembic initial migration; seed equipment |
| **Files** | `backend/app/models/*`; `alembic/versions/*` |
| **Dependencies** | Phase 0 |
| **Acceptance** | Migration up/down; five equipment rows |
| **Tests** | Migration smoke test |
| **DoD** | Schema matches docs |
| **Status** | DONE (2026-09-29) |

---

## Phase 2 — Scheduling domain/backend

| | |
|--|--|
| **Objective** | Services/repos for Batch, UnitOperation, Dependency |
| **Tasks** | CRUD helpers; seed ≥3 batches with ≥2 deliberate violations |
| **Files** | `services/scheduling.py`; `repositories/*`; `seed.py` |
| **Dependencies** | Phase 1 |
| **Acceptance** | Seed script loads demo schedule |
| **Tests** | Repository unit tests |
| **DoD** | Data available for validation phase |
| **Status** | DONE (2026-09-29) |

---

## Phase 3 — Scheduling validation

| | |
|--|--|
| **Objective** | Implement DR-001–DR-005 with exclusive ends |
| **Tasks** | Validator module; violation message formatting; pair dedupe |
| **Files** | `domain/scheduling_rules.py`; tests per rule |
| **Dependencies** | Phase 2 |
| **Acceptance** | All examples in `03-DOMAIN_RULES.md` pass |
| **Tests** | **Required:** exhaustive unit tests for each DR including Oct 1–4 vs Oct 4–6 non-overlap |
| **DoD** | Business-critical logic covered |
| **Status** | DONE (2026-09-29) |

---

## Phase 4 — Scheduling APIs

| | |
|--|--|
| **Objective** | Expose Part A endpoints per `05-API_CONTRACT.md` |
| **Tasks** | GET schedule; POST/PUT/DELETE unit ops; ADR-005 policy; error envelope |
| **Files** | `api/schedule.py`; `api/unit_operations.py`; schemas |
| **Dependencies** | Phase 3 |
| **Acceptance** | Contract examples work; violations on GET |
| **Tests** | API integration tests |
| **DoD** | Frontend can bind to real API |
| **Status** | DONE (2026-09-29) — ADR-005 Option B |

---

## Phase 5 — Gantt scheduler UI

| | |
|--|--|
| **Objective** | Part B Schedule page |
| **Tasks** | Lanes, date controls, blocks, envelopes, modal, highlight, violation list |
| **Files** | `frontend/src/pages/Schedule*`; components; api client |
| **Dependencies** | Phase 4 |
| **Acceptance** | Matches `07-FRONTEND_SPEC` mandatory items |
| **Tests** | Component/smoke tests as practical; manual desktop check |
| **DoD** | Demo path for Gantt + clear violation ready |
| **Status** | DONE (2026-09-29) — custom Gantt (ADR-006) |

---

## Phase 6 — Device simulator

| | |
|--|--|
| **Objective** | Replay run + response model + 1 Hz emit |
| **Tasks** | CSV loader; speed config; feed/DO lag step; clamp; process clock |
| **Files** | `simulator/*` |
| **Dependencies** | Phase 0; data_kit |
| **Acceptance** | Emits four signals/sec; command changes feed; DO responds with lag |
| **Tests** | Unit tests for response step and clamp |
| **DoD** | Simulator runnable standalone against mock ingest |
| **Status** | DONE (2026-09-29) — dry-run default; `--post-ingest` awaits Phase 7 |

---

## Phase 7 — Ingestion and persistence

| | |
|--|--|
| **Objective** | `POST /ingest` + reading storage; command table wiring prep |
| **Tasks** | Ingest service; process time tracking; optional control state GET |
| **Files** | `api/ingest.py`; models reading/command |
| **Dependencies** | Phases 1, 6 |
| **Acceptance** | Simulator readings persist and queryable |
| **Tests** | Ingest API tests |
| **DoD** | Data path ready for ML |
| **Status** | DONE (2026-09-29) — also GET /api/control/state extension |

---

## Phase 8 — ML forecasting

| | |
|--|--|
| **Objective** | 60→10 DO forecast + baseline eval + artifact |
| **Tasks** | Dataset split; train; evaluate vs persistence; `Forecaster` interface; append-only prediction store |
| **Files** | `app/ml/*`; training script; artifacts |
| **Dependencies** | Phase 7 |
| **Acceptance** | Held-out metrics documented; live forecast rows written |
| **Tests** | Evaluation script; interface unit test with baseline |
| **DoD** | README section draftable with real numbers |
| **Status** | DONE (2026-09-29) — Ridge MAE 0.498 vs persistence 0.576 on run_C |

---

## Phase 9 — Controller

| | |
|--|--|
| **Objective** | Emit validated setpoints with bounds, lag, dwell |
| **Tasks** | Rule policy; `POST /command` validation; reject persistence |
| **Files** | `services/controller.py`; `domain/command_validation.py` |
| **Dependencies** | Phases 7–8 (8 for optional forecast use; reactive can start after 7) |
| **Acceptance** | Loop can command; rejects stored |
| **Tests** | Command validation unit tests (all four reject reasons) |
| **DoD** | Closed loop without UI possible |
| **Status** | DONE (2026-09-29) — `POST /command`, `POST /api/control/step`, pending poll |

---

## Phase 10 — Live control UI

| | |
|--|--|
| **Objective** | Part C live page |
| **Tasks** | Charts, forecast overlay, markers, manual setpoint, rejects, process time |
| **Files** | `frontend/src/pages/Control*` |
| **Dependencies** | Phases 8–9 |
| **Acceptance** | `07-FRONTEND_SPEC` control requirements |
| **Tests** | Manual + light component tests |
| **DoD** | Demo path for control loop ready |
| **Status** | DONE (2026-09-29) — `/control` polls state; SVG charts; forecast + markers |

---

## Phase 11 — End-to-end integration

| | |
|--|--|
| **Objective** | Full demo script works locally |
| **Tasks** | Compose run instructions; fix gaps; deliberate violation walkthrough |
| **Files** | `docs/DEMO_SCRIPT.md`; `scripts/demo-prep.ps1`; `scripts/e2e-check.ps1`; simulator `--poll-commands` |
| **Dependencies** | Phases 5 and 10 |
| **Acceptance** | ≤3 min demo script executable |
| **Tests** | E2E checklist manual + `e2e-check.ps1` |
| **DoD** | Ready for recording |
| **Status** | DONE (2026-09-29) |

---

## Phase 12 — Automated testing

| | |
|--|--|
| **Objective** | Harden CI-worthy suite |
| **Tasks** | Expand rule/command/API tests; document how to run |
| **Dependencies** | Phases 3–9 |
| **Acceptance** | Critical paths covered; documented in README |
| **DoD** | Test command green locally |
| **Status** | DONE (2026-09-29) — shared conftest; command reject coverage; smoke includes sim tests |

---

## Phase 13 — Deployment

| | |
|--|--|
| **Objective** | Hosted application URL (required) |
| **Tasks** | Choose host (ADR-008); deploy API+UI+DB; configure secrets |
| **Dependencies** | Phase 11 |
| **Acceptance** | Non-technical user can open hosted app |
| **DoD** | URL in README (no fabricated URL before real deploy) |

---

## Phase 14 — Documentation and demo

| | |
|--|--|
| **Objective** | Submission completeness |
| **Tasks** | Fill README required headings; PROMPTS.md; record ≤3 min video; repo invites |
| **Dependencies** | Phase 13 |
| **Acceptance** | Assignment §4 deliverables |
| **DoD** | Ready to submit |

---

## Optional extensions

Only after Phases 0–14 mandatory acceptance criteria are met:

- E1 AI scheduling assistant  
- E2 Forecast-aware controller  
- E3 Drag to reschedule  
- E4 Multiple vessels  

Mark clearly in README if pursued.

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Phased plan 0–14 |
