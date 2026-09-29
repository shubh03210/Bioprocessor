# Requirements Checklist

Traceability from `Take_Home_SWE_ML_Brief.pdf` (+ `data_kit`).  
**Initial status for all items: NOT STARTED** (documentation existence does not mark complete).

Legend: `NOT STARTED` | `IN PROGRESS` | `DONE` | `BLOCKED`

---

## Part A — Scheduling Backend

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| A-001 | Model Equipment (id, name); seed 1.5L, 15L, 20L, 75L, 1500L | Part A Entities | DONE |
| A-002 | Model Batch (id, name, start_date, end_date) | Part A Entities | DONE |
| A-003 | Model UnitOperation (id, name, type, color, status, start_date, end_date, batch_id, equipment_id) | Part A Entities | DONE |
| A-004 | type ∈ {Seed, Bioreactor, TFF, Spray, Sum} | Part A Entities | DONE (CHECK constraint) |
| A-005 | status ∈ {draft, confirmed, completed} | Part A Entities | DONE (CHECK constraint) |
| A-006 | Model UnitOperationDependency (id, from_unitop_id, to_unitop_id) | Part A Entities | DONE |
| A-007 | Treat end dates as exclusive | Part A Business rules intro | DONE |
| A-008 | DR-001 Batch containment | Part A Rule 1 | DONE |
| A-009 | DR-002 Process ordering (later type not before every earlier type ended) | Part A Rule 2 | DONE |
| A-010 | DR-003 No equipment double-booking across batches | Part A Rule 3 | DONE |
| A-011 | DR-004 Explicit dependency ordering | Part A Rule 4 | DONE |
| A-012 | DR-005 Completed ops cannot be moved or deleted | Part A Rule 5 | DONE |
| A-013 | Readable violation messages naming operations involved | Part A Rules | DONE |
| A-014 | Report each violating pair once per rule | Part A Rules | DONE |
| A-015 | Save on violation does not silently succeed (reject OR save-and-return) | Part A Behavior on save | DONE (save-and-return; DR-005 rejects) |
| A-016 | Document chosen save behavior in README | Part A Behavior on save | DONE |
| A-017 | Persist to a database | Part A API | DONE |
| A-018 | GET /api/schedule?start_date&end_date returns grid data + violations | Part A API | DONE |
| A-019 | POST /api/unit_operations | Part A API | DONE |
| A-020 | PUT /api/unit_operations/{op_id} | Part A API | DONE |
| A-021 | DELETE /api/unit_operations/{op_id} | Part A API | DONE |
| A-022 | Seed ≥3 batches across equipment | Part A Seed data | DONE |
| A-023 | Seed ≥2 deliberate rule violations for Part B | Part A Seed data | DONE |

---

## Part B — Scheduler UI

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| B-001 | Gantt-style grid | Part B | DONE |
| B-002 | Y-axis equipment lanes | Part B | DONE |
| B-003 | X-axis scrollable date range | Part B | DONE |
| B-004 | Controls to choose visible start and end dates | Part B | DONE |
| B-005 | Color-coded unit operation blocks on equipment lane | Part B | DONE |
| B-006 | Batch envelope visual grouping | Part B | DONE |
| B-007 | Click opens modal/drawer | Part B | DONE |
| B-008 | Edit start, end, equipment, status | Part B | DONE |
| B-009 | Equipment picker from predefined list | Part B | DONE |
| B-010 | Highlight backend-reported violations | Part B | DONE |
| B-011 | Violation message on hover or in a list | Part B | DONE |
| B-012 | Desktop only | Part B | DONE |

---

## Part C — Closed-Loop Control

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| C-001 | Keep process time and wall-clock separate | Part C intro | DONE (time_h + created_at) |
| C-002 | Stamp readings, forecasts, commands with process time | Part C intro | DONE |
| C-003 | Device simulator emits DO, pH, temp, feed_rate once per second | Part C.1 | DONE |
| C-004 | Simulator replays a fermentation run | Part C.1 / §3 | DONE |
| C-005 | Simulator accepts feed-rate command and applies response model | Part C.1 / §3 | DONE (local FeedCommand; API poll ready via `/api/control/commands/pending`) |
| C-006 | Ingest API receives readings and writes DB | Part C.2 | DONE |
| C-007 | Tables for readings, predictions, control commands | Part C.2 | DONE |
| C-008 | Predictions stored with process time made at; never overwritten | Part C.2 | DONE |
| C-009 | Forecaster: last 60 min DO + feed → next 10 min DO @ 1-min | Part C.3 | DONE |
| C-010 | Report error on held-out data vs persistence baseline | Part C.3 | DONE |
| C-011 | Document train/hold-out split | Part C.3 / data_kit | DONE |
| C-012 | Controller emits feed setpoint (rule OK if justified) | Part C.4 | DONE |
| C-013 | Respect feed bounds from §3 / limits.json | Part C.4 / §3 | DONE |
| C-014 | Respect 5-minute actuator lag | Part C.4 | DONE |
| C-015 | Respect dwell time between commands | Part C.4 | DONE (5 process-min; ADR-015) |
| C-016 | Live page: DO and feed traces | Part C.5 | DONE |
| C-017 | Live page: latest forecast overlaid | Part C.5 | DONE |
| C-018 | Live page: commands marked on time axis | Part C.5 | DONE |
| C-019 | Live page: manual setpoint input | Part C.5 | DONE |
| C-020 | Polling every few seconds acceptable | Part C.5 | DONE (2.5 s) |
| C-021 | Validate all commands (controller or human) | Command validation | DONE |
| C-022 | Reject: value outside bounds | Command validation | DONE |
| C-023 | Reject: apply time earlier than current process time | Command validation | DONE |
| C-024 | Reject: unit does not match | Command validation | DONE |
| C-025 | Reject: another command for same setpoint still pending | Command validation | DONE |
| C-026 | Store rejected commands with reason | Command validation | DONE |
| C-027 | Show rejected commands on live page | Command validation | DONE |
| C-028 | Configurable replay speed; default ~1 process-min / wall-sec | §3 | DONE |
| C-029 | Device response: feed follows setpoint after t0 | §3 | DONE |
| C-030 | Device response: dDO FO lag τ=5, g=2.0; clamp DO [0,100] | §3 | DONE |
| C-031 | Implement response as simple step each second; document deviations | §3 | DONE |
| C-032 | POST /ingest contract | §3 | DONE |
| C-033 | POST /command contract | §3 | DONE |
| C-034 | Feed limits 0.0–30.0 mL/h | §3 / limits.json | DONE |

---

## Data / Contracts

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| D-001 | Support run CSV schema time_h,signal_name,value,unit | §3 / data_kit | NOT STARTED |
| D-002 | Use provided runs or document synthesis | §3 | NOT STARTED |
| D-003 | Signals DO, pH, temp, feed_rate with correct units | §3 | NOT STARTED |

---

## Submission

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| S-001 | Private GitHub repo named `<your_name>_bbp` | §4.1 | NOT STARTED |
| S-002 | Invite VinitBB and FanLu55 | §4.1 | NOT STARTED |
| S-003 | Hosted link to running application | §4.2 | NOT STARTED |
| S-004 | Hosting required; Docker not required | §4.2 | DONE (packaging; no Docker) |
| S-005 | Screen recording ≤3 minutes | §4.3 | NOT STARTED |
| S-006 | Demo shows Gantt with violations highlighted | §4.3 | NOT STARTED |
| S-007 | Demo shows edit clearing a violation | §4.3 | NOT STARTED |
| S-008 | Demo shows control loop: readings, forecast, command, device response | §4.3 | NOT STARTED |
| S-009 | README: how to run locally | §4.4 | NOT STARTED |
| S-010 | README: hosted URL | §4.4 | NOT STARTED |
| S-011 | README: How I split and evaluated the forecaster | §4.4 | DONE |
| S-012 | README: Decisions and trade-offs (≥2) | §4.4 | NOT STARTED |
| S-013 | README: How I would deploy, retrain and monitor this | §4.4 | NOT STARTED |
| S-014 | README: seed data and where deliberate violations are | §4.4 | NOT STARTED |
| S-015 | PROMPTS.md with tools, models, verbatim prompts, changes, mistakes | §4.5 | NOT STARTED |

---

## Documentation (project governance)

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| G-001 | Specs and Cursor rules bootstrap | Internal Phase docs | DONE (docs only) |
| G-002 | Phase 0 project foundation (scaffold, health, install) | Implementation plan Phase 0 | DONE |
| G-003 | Phase 1 database and migrations | Implementation plan Phase 1 | DONE |
| G-004 | Phase 2 scheduling domain/backend + demo seed | Implementation plan Phase 2 | DONE |
| G-005 | Phase 3 scheduling validation DR-001–DR-005 | Implementation plan Phase 3 | DONE |
| G-006 | Phase 4 scheduling APIs | Implementation plan Phase 4 | DONE |
| G-007 | Phase 5 Gantt scheduler UI | Implementation plan Phase 5 | DONE |
| G-008 | Phase 6 device simulator | Implementation plan Phase 6 | DONE |
| G-009 | Phase 7 ingest and persistence | Implementation plan Phase 7 | DONE |
| G-010 | Phase 8 ML forecasting | Implementation plan Phase 8 | DONE |
| G-011 | Phase 9 controller + command validation | Implementation plan Phase 9 | DONE |
| G-012 | Phase 10 live control UI | Implementation plan Phase 10 | DONE |
| G-013 | Phase 11 E2E demo / integration | Implementation plan Phase 11 | DONE |
| G-014 | Phase 12 automated testing | Implementation plan Phase 12 | DONE |
| G-015 | Phase 13 hosting packaging (await live URL) | Implementation plan Phase 13 | DONE (packaging); URL NOT STARTED |

---

## Optional Extensions (not mandatory)

Do not start until mandatory Part A–C + submission essentials for demo are complete.

| ID | Requirement | Source | Status |
|----|-------------|--------|--------|
| E1-001 | AI scheduling assistant (NL + tools + HITL + design) | §5 E1 | NOT STARTED (OPTIONAL) |
| E2-001 | Forecast-aware controller | §5 E2 | NOT STARTED (OPTIONAL) |
| E3-001 | Drag to reschedule | §5 E3 | NOT STARTED (OPTIONAL) |
| E4-001 | Multiple vessels | §5 E4 | NOT STARTED (OPTIONAL) |

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Full mandatory checklist; all NOT STARTED except G-001 |
