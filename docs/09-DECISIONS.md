# Architecture Decision Records

**Document ID:** `09-DECISIONS`  
**Rule:** Do not pretend a decision is final when Status is OPEN. Update this file when decisions change.

---

## ADR-001 — Backend stack

| Field | Content |
|-------|---------|
| **Decision** | Use FastAPI + Pydantic + SQLAlchemy/SQLModel + Alembic |
| **Context** | Assignment recommends this stack; team needs rapid PoC with clear validation |
| **Options** | FastAPI stack; Django; Node/Express; other |
| **Chosen approach** | FastAPI stack as recommended |
| **Reason** | Matches assignment guidance; strong typing via Pydantic; good fit for ML-in-Python |
| **Trade-offs** | Python packaging/deploy vs Node unification; acceptable for PoC |
| **Status** | ACCEPTED |

---

## ADR-002 — Database

| Field | Content |
|-------|---------|
| **Decision** | SQLite for local/dev PoC with PostgreSQL-compatible schema; production/hosted may use PostgreSQL |
| **Context** | Assignment allows SQLite or PostgreSQL |
| **Options** | SQLite only; PostgreSQL only; SQLite→Postgres path |
| **Chosen approach** | SQLite locally; keep migrations portable |
| **Reason** | Fastest setup for take-home; hosting can switch DATABASE_URL |
| **Trade-offs** | Concurrency limits on SQLite under load — fine for PoC |
| **Status** | ACCEPTED |

---

## ADR-003 — Frontend technology

| Field | Content |
|-------|---------|
| **Decision** | React + TypeScript |
| **Context** | Assignment recommends React |
| **Options** | React; Vue; Svelte; server-rendered only |
| **Chosen approach** | React + TypeScript SPA |
| **Reason** | Recommendation + ecosystem for charts/Gantt |
| **Trade-offs** | Build tooling overhead vs vanilla |
| **Status** | ACCEPTED |

---

## ADR-004 — API style

| Field | Content |
|-------|---------|
| **Decision** | REST JSON endpoints exactly as assignment minimum paths |
| **Context** | Assignment specifies paths for schedule and ingest/command |
| **Options** | REST; GraphQL; RPC |
| **Chosen approach** | REST as specified |
| **Reason** | Comparability with assignment contracts |
| **Trade-offs** | Extra poll endpoints may be needed for live UI |
| **Status** | ACCEPTED |

---

## ADR-005 — Violation save policy

| Field | Content |
|-------|---------|
| **Decision** | Save-and-return violations (Option B) |
| **Context** | Assignment allows reject or save-and-return; seed data needs visible violations |
| **Options** | (A) Reject with messages; (B) Persist and return violations for highlighting |
| **Chosen approach** | Option B for create/update of unit operations (except DR-005 which always rejects) |
| **Reason** | Matches Part B highlighting of seeded violations; demo can show conflicts without a seed bypass; DR-005 still hard-blocks completed moves/deletes |
| **Trade-offs** | Schedule can contain known-invalid state until edited |
| **Status** | ACCEPTED |

---

## ADR-006 — Gantt implementation

| Field | Content |
|-------|---------|
| **Decision** | Custom CSS timeline (no third-party scheduler library) |
| **Context** | Assignment allows open-source scheduler or custom; no paid libs |
| **Options** | Custom grid; open-source resource timeline library |
| **Chosen approach** | Custom absolutely-positioned day grid with equipment lanes |
| **Reason** | Full control for batch envelopes + violation styling; keeps deps light for PoC |
| **Trade-offs** | More UI code to maintain; no drag-and-drop until E3 |
| **Status** | ACCEPTED |

---

## ADR-007 — ML model selection

| Field | Content |
|-------|---------|
| **Decision** | Use Ridge multi-output linear (`ridge-linear-v1`) as the live forecaster |
| **Context** | Assignment allows GRU/LSTM/linear/GB/etc.; closed loop > accuracy; must beat persistence baseline on held-out data |
| **Options** | Persistence-only; linear/Ridge; GBDT; GRU/LSTM |
| **Chosen approach** | Interface-first `Forecaster` protocol; train Ridge on run_A+B; hold out run_C; ship Ridge if MAE < persistence (it did: 0.498 vs 0.576) |
| **Reason** | Smallest model that meaningfully beats baseline; fast to train/load; swappable via artifact |
| **Trade-offs** | Weaker on strongly nonlinear DO crashes than GRU/GBDT; acceptable for PoC closed loop |
| **Status** | ACCEPTED |

---

## ADR-008 — Hosting

| Field | Content |
|-------|---------|
| **Decision** | TBD hosting provider |
| **Context** | Hosting required; Docker not required |
| **Options** | Railway, Render, Fly.io, Vercel+separate API, etc. |
| **Chosen approach** | TBD in Phase 13 |
| **Reason** | Depends on final process model (simulator process needs to run) |
| **Trade-offs** | Free-tier sleep vs always-on for demo |
| **Status** | OPEN |

---

## ADR-009 — Scheduling validation location

| Field | Content |
|-------|---------|
| **Decision** | Server-side domain module is sole authority |
| **Context** | Assignment requires backend enforcement |
| **Options** | Backend only; frontend only; both authoritative |
| **Chosen approach** | Backend only as authority; frontend displays results |
| **Reason** | Single source of truth |
| **Trade-offs** | Extra round-trip for every edit |
| **Status** | ACCEPTED |

---

## ADR-010 — Process-time representation

| Field | Content |
|-------|---------|
| **Decision** | Store process time as float hours (`time_h`) consistent with data_kit; wall-clock as UTC timestamps |
| **Context** | Assignment requires separation and process-time stamps |
| **Options** | float hours; integer minutes; datetime process clock |
| **Chosen approach** | float hours |
| **Reason** | Matches CSV contract and ingest/command schemas |
| **Trade-offs** | Float precision — acceptable at 1-minute grid |
| **Status** | ACCEPTED |

---

## ADR-011 — Simulator architecture

| Field | Content |
|-------|---------|
| **Decision** | Separate simulator module/process speaking HTTP to `/ingest` and `/command` |
| **Context** | Device pushes readings; accepts commands |
| **Options** | In-process thread; separate process; external mock |
| **Chosen approach** | Separate runnable process (may share repo) |
| **Reason** | Clear isolation; closer to real device |
| **Trade-offs** | Ops complexity on host |
| **Status** | ACCEPTED |

---

## ADR-012 — Error handling strategy

| Field | Content |
|-------|---------|
| **Decision** | Unified JSON error envelope with codes in `05-API_CONTRACT.md` |
| **Context** | Need consistent UI handling |
| **Options** | Ad-hoc strings; RFC7807; custom envelope |
| **Chosen approach** | Custom envelope documented in API contract |
| **Reason** | Simple for PoC |
| **Trade-offs** | Not standard Problem Details |
| **Status** | ACCEPTED |

---

## ADR-013 — Dependency / unit-op FK delete behavior

| Field | Content |
|-------|---------|
| **Decision** | Use `ON DELETE RESTRICT` for unit operation FKs (batch, equipment, dependency endpoints) |
| **Context** | `04-DATABASE_DESIGN.md` left CASCADE vs RESTRICT open |
| **Options** | RESTRICT; CASCADE |
| **Chosen approach** | RESTRICT |
| **Reason** | Prevent accidental schedule graph deletion; clearer audit for PoC |
| **Trade-offs** | Deletes require removing dependencies first |
| **Status** | ACCEPTED |

---

## ADR-014 — Completed operation update policy (DR-005)

| Field | Content |
|-------|---------|
| **Decision** | Block delete; block changes to dates/equipment/status on `completed`; allow identical no-op updates |
| **Context** | Assignment forbids move/delete of completed ops; status change unspecified |
| **Options** | Reject all updates; allow status-only; allow no-op only |
| **Chosen approach** | No-op allowed; status demotion blocked |
| **Reason** | Matches “cannot be moved”; prevents quietly reopening completed work |
| **Trade-offs** | Operators must create a new op instead of reopening |
| **Status** | ACCEPTED |

---

## ADR-015 — Reactive controller policy and dwell

| Field | Content |
|-------|---------|
| **Decision** | Rule-based reactive feed controller; dwell = 5 process-minutes; lag applied as `apply_at = now + 5/60 h` |
| **Context** | Assignment allows rule-based control if justified; requires bounds, 5-min lag, dwell; dwell value unspecified |
| **Options** | Reactive DO thresholds; forecast-aware (E2 deferred); PID |
| **Chosen approach** | Decrease feed when DO < 50% (stronger if < 35%); increase modestly when DO > 75% and feed not high; deadband otherwise. All emissions go through `POST /command` validation. Pending commands with `apply_at <= current` auto-mark `applied` before new validation |
| **Reason** | Overfeeding crashes DO; closed loop demo without needing E2 |
| **Trade-offs** | Thresholds are heuristics; not process-tuned |
| **Status** | ACCEPTED |

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial ADRs; several OPEN |
| 0.2 | 2026-09-29 | ADR-013 FK ondelete RESTRICT |
| 0.3 | 2026-09-29 | ADR-014 DR-005 completed immutability detail |
| 0.4 | 2026-09-29 | ADR-005 Option B accepted |
| 0.5 | 2026-09-29 | ADR-006 custom Gantt accepted |
| 0.6 | 2026-09-29 | ADR-007 Ridge linear accepted after hold-out eval |
| 0.7 | 2026-09-29 | ADR-015 reactive controller + dwell |
