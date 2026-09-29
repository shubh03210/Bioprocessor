# Project Specification

**Document ID:** `01-PROJECT_SPEC`  
**Source of truth hierarchy:** Assignment PDF > data_kit > this document > other docs > Cursor rules > code  
**Primary source:** `Take_Home_SWE_ML_Brief.pdf`  
**Status:** Specification only — no application implementation in this phase  

---

## 1. Purpose

Build a proof-of-concept desktop web application for Boston Bioprocess that:

1. Replaces spreadsheet-based batch/unit-operation scheduling with a single source of truth that enforces scheduling business rules.
2. Demonstrates a closed-loop bioreactor control path: device readings → storage → DO forecast → feed setpoint command → live visualization.

The product is evaluated on functionality, code quality, judgment, and a short demo — not on production scale or paid libraries.

---

## 2. Problem Statement

Manufacturing batches are sequences of interdependent unit operations (Seed, Bioreactor, TFF, Spray, Sum) that run on scarce equipment (1.5L, 15L, 20L, 75L, 1500L). Today coordination happens in spreadsheets, which is slow, error-prone (e.g., double-booking), and hard to change quickly. A scheduling error can lose a batch and cost significant capital and time.

Separately, once a batch runs, operators manually watch dissolved oxygen (DO) and adjust the feed pump. Overfeeding crashes DO and cells starve. A real-time loop is needed: device pushes readings, backend stores them, a model forecasts DO, a controller sends a feed setpoint, and a live page shows the loop.

---

## 3. Project Goals

| Goal | Description |
|------|-------------|
| G1 | Persist schedule entities and enforce Part A business rules server-side |
| G2 | Expose schedule APIs sufficient for a Gantt UI with violation visibility |
| G3 | Provide a desktop Gantt scheduler UI (equipment lanes, batch envelopes, edit modal/drawer) |
| G4 | Close a single-vessel control loop with process-time simulation faster than wall-clock |
| G5 | Forecast next 10 minutes of DO (1-min resolution) from last 60 minutes of DO and feed rate |
| G6 | Validate and persist control commands (accepted and rejected) |
| G7 | Deliver hosted app, ≤3-minute demo, README, and PROMPTS.md per assignment §4 |

Non-goals are listed in §12. Optional extensions (E1–E4) are out of scope until all mandatory work is done.

---

## 4. Assignment Scope

| Part | Scope |
|------|--------|
| **Part A** | Scheduling data model, persistence, business rules, minimal schedule APIs, seed data with deliberate violations |
| **Part B** | Desktop Gantt scheduler UI consuming Part A APIs |
| **Part C** | Device simulator, ingest, forecaster, controller, command validation, live control page |
| **Submission** | Private GitHub repo, hosted link, ≤3 min recording, README, PROMPTS.md |
| **Optional** | E1–E4 — explicitly deferred until mandatory requirements are complete |

**Repository naming (assignment):** `<your_name>_bbp`, invite `VinitBB` and `FanLu55`.  
**Working folder for this bootstrap:** `bbp-scheduling/` (rename/align to submission name later — Design Decision / Implementation Choice).

---

## 5. Part A — Scheduling Backend

### 5.1 Entities (assignment starting point; may be extended)

| Entity | Fields (assignment) |
|--------|---------------------|
| Equipment | `id`, `name` — seed: `1.5L`, `15L`, `20L`, `75L`, `1500L` |
| Batch | `id`, `name`, `start_date`, `end_date` |
| UnitOperation | `id`, `name`, `type`, `color`, `status`, `start_date`, `end_date`, `batch_id`, `equipment_id` |
| UnitOperationDependency | `id`, `from_unitop_id`, `to_unitop_id` — explicit “must finish before” link |

**Unit operation types:** `Seed`, `Bioreactor`, `TFF`, `Spray`, `Sum` (process order).  
**Unit operation statuses:** `draft`, `confirmed`, `completed`.

### 5.2 Interval semantics

**End dates are exclusive.** An operation that ends on November 4 frees its equipment on November 4.  
Example: Oct 1 → Oct 4 and Oct 4 → Oct 6 do **not** overlap.

### 5.3 Business rules (must enforce)

1. **Batch containment** — every unit operation of a batch lies within the batch start/end.
2. **Process ordering** — later type may not start before every earlier type in the same batch has ended. Types need not all be present. Example: Seed Oct 21–24 → Bioreactor may start Oct 24, not Oct 23.
3. **Equipment double-booking** — same equipment cannot be used by two unit operations at the same time (any batch).
4. **Explicit dependency** — dependency target may not start before source has ended.
5. **Completed immutability** — a completed unit operation cannot be moved or deleted.

Violations: readable message naming operations involved; each violating pair once per rule.

### 5.4 Behavior on save

Saving a unit operation that violates a rule must **not** silently succeed:

- **Option A:** reject the save with violation messages, **or**
- **Option B:** save and return violations so the UI can highlight the operation.

Choice must be documented in README.  
**Status:** Design Decision / Implementation Choice — see `09-DECISIONS.md` (ADR-005).

### 5.5 Required APIs (minimum)

```text
GET    /api/schedule?start_date=...&end_date=...
POST   /api/unit_operations
PUT    /api/unit_operations/{op_id}
DELETE /api/unit_operations/{op_id}
```

`GET /api/schedule` must return all data needed for the grid in that range, including current violations.

### 5.6 Seed data

Load at least **three batches** across the equipment, with at least **two deliberate rule violations** so Part B highlighting is visible immediately.

---

## 6. Part B — Scheduler UI

Mandatory UI requirements:

- Gantt-style grid: **y** = equipment lanes; **x** = scrollable date range with controls for visible start/end.
- Unit operations as color-coded blocks on equipment lanes.
- All unit operations of one batch grouped visually into a **batch envelope** (as in assignment Figure 1).
- Click opens modal or drawer to edit start, end, equipment (from predefined list), and status.
- Backend-reported violating operations visually highlighted (e.g., red border / alert); message on hover or in a list.
- **Desktop only.** Look and feel beyond the above is open.

Frontend must **not** be the authoritative source of scheduling validation.

---

## 7. Part C — Closed-Loop Bioreactor Control

Five pieces forming one closed loop (a closed loop matters more than an accurate model):

1. **Device simulator** — emits DO, pH, temperature, feed rate **once per second** by replaying a fermentation run; accepts feed-rate commands; applies response model (§ assignment §3).
2. **Ingest API and store** — receives pushed readings; tables for readings, predictions, and control commands at minimum. Predictions stamped with process time made at; **never overwritten**.
3. **Forecaster** — predicts next **10 minutes** of DO at **1-minute** resolution from last **60 minutes** of DO and feed rate. Report error on held-out data vs **persistence baseline** (repeat last value); document split.
4. **Controller** — rule or model-informed policy emitting feed setpoint. Rule-based acceptable if justified. Respect feed bounds, **5-minute actuator lag**, and dwell time between commands.
5. **Live page** — DO and feed traces, latest forecast overlaid, commands marked on time axis, manual setpoint input. Polling every few seconds is enough.

### 7.1 Process time vs wall-clock

Keep process time and wall-clock time separate. Stamp readings, forecasts, and commands with **process time**. Simulate process faster than wall-clock so operators never wait real minutes/hours.

Default sensible replay: **one process-minute per wall-clock second** (configurable). Recording may run faster or start mid-run.

### 7.2 Command validation

Backend validates every command (controller or human) and rejects with a reason when:

- value outside bounds,
- apply time earlier than device’s current process time,
- unit does not match,
- another command for the same setpoint is still pending.

Store rejected commands with reason; show on live page.

### 7.3 Data contracts

**Runs:** `run_A.csv`, `run_B.csv`, `run_C.csv` (~40 h each); columns `time_h,signal_name,value,unit`. Signals: DO (%), pH (-), temp (degC), feed_rate (mL/h). May synthesize equivalent runs; document in README.

**Limits:** `{"feed_rate": {"unit": "mL/h", "min": 0.0, "max": 30.0}}` (see `data_kit/limits.json`).

**Ingest:** `POST /ingest` with readings array.  
**Command:** `POST /command` with setpoint fields (see `05-API_CONTRACT.md`).

**Device response** (command applied at process time `t0`):

- `feed_rate(t) = setpoint` for `t >= t0` until next command.
- `DO(t) = DO_run(t) + dDO(t)`, where `dDO` first-order lag toward `-g * (feed_rate(t) - feed_run(t))` with `τ = 5` process-minutes, `g = 2.0` %DO per mL/h. Clamp DO to `[0, 100]`.
- Implement as a simple step each second; document any deviation.

---

## 8. Required Technologies

### 8.1 Assignment recommendations (not mandatory)

| Layer | Recommendation |
|-------|----------------|
| UI | React |
| Backend | FastAPI (Python) |
| Database | PostgreSQL (SQLite acceptable) |
| ORM/migrations | SQLModel and Alembic if using that stack |
| Gantt | Any open-source resource-timeline library, or custom CSS Grid/Flexbox; no paid library expected |

Any other stack is allowed. Evaluation focuses on functionality and code quality.

### 8.2 Selected implementation choices

| Concern | Choice | Status |
|---------|--------|--------|
| Backend | FastAPI + Pydantic | Selected (ADR-001) |
| ORM | SQLAlchemy / SQLModel | Selected (ADR-001) |
| Migrations | Alembic | Selected (ADR-001) |
| Database | SQLite for local PoC; PostgreSQL-compatible schema | Selected with path to Postgres (ADR-002) |
| Frontend | React + TypeScript | Selected (ADR-003) |
| API style | REST JSON as specified | Selected (ADR-004) |
| Gantt library | TBD | OPEN (ADR-006) |
| ML model family | TBD after baseline comparison | OPEN (ADR-007) |
| Hosting provider | TBD | OPEN (ADR-008) |
| Violation save policy | Reject vs save-and-return | OPEN (ADR-005) |

Anything not listed remains **Design Decision / Implementation Choice** until recorded in `09-DECISIONS.md`.

---

## 9. Required APIs

| Method | Path | Part |
|--------|------|------|
| GET | `/api/schedule?start_date=&end_date=` | A |
| POST | `/api/unit_operations` | A |
| PUT | `/api/unit_operations/{op_id}` | A |
| DELETE | `/api/unit_operations/{op_id}` | A |
| POST | `/ingest` | C |
| POST | `/command` | C |

Additional endpoints (e.g., live readings poll, health) are **implementation extensions** and must be documented in `05-API_CONTRACT.md` before use — not invented as assignment requirements.

---

## 10. Required Deliverables

1. Code in private GitHub repo named `<your_name>_bbp`; invite `VinitBB` and `FanLu55` (emails in assignment §4).
2. Hosted link to running application (hosting required; Docker is not).
3. Screen recording ≤ **3 minutes** (in repo or linked from README) showing: Gantt with violations highlighted; edit in modal that clears a violation; control loop closing (readings, forecast, command, device response).
4. `README.md` — local run, hosted URL, headings: *How I split and evaluated the forecaster*; *Decisions and trade-offs* (≥2 from backend/frontend/ML); *How I would deploy, retrain and monitor this*; seed data and where deliberate violations are.
5. `PROMPTS.md` if AI used — tools/models; prompts verbatim in order; what changed; what AI got wrong.

---

## 11. Optional Extensions

**Do base tasks first.** Mark any extension clearly in README. Do **not** implement until mandatory requirements are complete and tested.

| ID | Name | Summary |
|----|------|---------|
| E1 | AI scheduling assistant | NL schedule changes via tools calling Part A APIs; structured proposal; human-in-the-loop; deployment design |
| E2 | Forecast-aware controller | Act on forecast ~1 lag ahead; document stale/missing forecast; show earlier action vs reactive |
| E3 | Drag to reschedule | Drag op to day/lane; save via update; inline violations; consistency during drag |
| E4 | Multiple vessels | ≥2 simulated vessels; document ingest/store/controller changes and 50-vessel breakage point |

---

## 12. Explicit Non-Goals

- Production multi-tenant SaaS, auth/SSO, RBAC (unless later chosen as Design Decision).
- Mobile / responsive scheduler UI (desktop only).
- Paid Gantt libraries.
- Turning optional extensions into mandatory scope.
- Inventing scheduling rules beyond assignment § Part A.
- Claiming forecast accuracy as the success criterion over a closed loop.
- Implementing application code in the documentation bootstrap phase.

---

## 13. Acceptance Criteria

### Part A
- [ ] Equipment seeded with five named vessels.
- [ ] Batches, unit ops, dependencies persist.
- [ ] All five business rules enforced with exclusive end dates.
- [ ] Violations reported with readable messages naming ops; once per violating pair per rule.
- [ ] Save does not silently succeed on violations (reject or save-and-return; documented).
- [ ] Required schedule CRUD/list APIs work.
- [ ] ≥3 batches seeded; ≥2 deliberate violations present.

### Part B
- [ ] Equipment-lane Gantt with scrollable date range controls.
- [ ] Color-coded ops; batch envelopes.
- [ ] Edit modal/drawer: start, end, equipment, status.
- [ ] Violations highlighted with accessible messages.
- [ ] Desktop-focused UI.

### Part C
- [ ] Simulator emits four signals once per second; configurable speed; process vs wall-clock separated.
- [ ] Response model matches assignment (τ=5, g=2.0, clamp DO).
- [ ] Ingest persists readings; predictions never overwritten; commands stored.
- [ ] Forecaster: 60-min history → 10-min DO @ 1-min; held-out vs persistence baseline documented.
- [ ] Controller respects bounds, 5-min lag, dwell; commands validated; rejects persisted and shown.
- [ ] Live page: DO/feed, forecast, command markers, manual setpoint; polling OK.

### Submission
- [ ] Private repo, invites, hosted URL, ≤3 min demo, README sections, PROMPTS.md.

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial spec from assignment PDF + data_kit |
