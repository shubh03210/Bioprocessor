# AI Prompts

Chronological record of AI usage for this assignment.  
Using AI is allowed; omitting this file when AI was used is not.

---

## Prompt 001 — Project Documentation Bootstrap

**Tool:**  
Cursor

**Model:**  
TODO — fill with the Cursor model name used for this session

**Date:**  
2026-09-29

**Purpose:**  
Create project specification and engineering governance files only (no application implementation). Produce `docs/`, `.cursor/rules/`, `README.md`, `REQUIREMENTS_CHECKLIST.md`, and `PROMPTS.md` under `bbp-scheduling/`, grounded in `Take_Home_SWE_ML_Brief.pdf` and `data_kit/`.

**Prompt:**  

```text
You are acting as the Lead Software Architect and Technical Specification Engineer for this project.

IMPORTANT:
Do NOT implement the application yet.
Do NOT create backend/frontend application code yet.
Your task in this step is ONLY to create the project's specification, architecture, engineering rules, implementation plan, and Cursor rules that will guide all future development.

==================================================
PROJECT CONTEXT
==================================================

The project is a take-home assignment titled:

"Take-Home Assignment: Bioprocess Scheduling and Closed-Loop Control"

The assignment PDF is present in the repository:

Take_Home_SWE_ML_Brief.pdf

The repository also contains the provided data kit:

data_kit/
data_kit.zip

The assignment PDF is the PRIMARY SOURCE OF TRUTH.

You MUST inspect and understand the assignment PDF before creating the documentation.

You MUST also inspect the data kit if it is accessible, because the assignment references provided fermentation runs such as run_A.csv, run_B.csv and run_C.csv.

Do not replace assignment requirements with your own assumptions.

If something is not specified by the assignment, explicitly mark it as:
"Design Decision / Implementation Choice"

Do not silently invent requirements.

==================================================
PRIMARY OBJECTIVE
==================================================

Create the following documentation and Cursor rule structure:

bbp-scheduling/
│
├── .cursor/
│   └── rules/
│       ├── 00-project-rules.mdc
│       ├── 01-architecture-rules.mdc
│       ├── 02-backend-rules.mdc
│       ├── 03-frontend-rules.mdc
│       └── 04-ml-control-rules.mdc
│
├── docs/
│   ├── 01-PROJECT_SPEC.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-DOMAIN_RULES.md
│   ├── 04-DATABASE_DESIGN.md
│   ├── 05-API_CONTRACT.md
│   ├── 06-ML_CONTROL_SPEC.md
│   ├── 07-FRONTEND_SPEC.md
│   ├── 08-IMPLEMENTATION_PLAN.md
│   └── 09-DECISIONS.md
│
├── README.md
├── REQUIREMENTS_CHECKLIST.md
└── PROMPTS.md

Do not create unnecessary additional documentation files unless absolutely required.

==================================================
SOURCE-OF-TRUTH HIERARCHY
==================================================

Use this hierarchy:

1. Take_Home_SWE_ML_Brief.pdf
2. Provided data_kit contents
3. docs/01-PROJECT_SPEC.md
4. Other docs in docs/
5. .cursor/rules/
6. Implementation code

If any future implementation conflicts with the assignment PDF, the assignment PDF wins.

If two design documents conflict, update the lower-level document rather than silently changing the requirement.

==================================================
STEP 1 — ANALYZE THE ASSIGNMENT
==================================================

Before writing the documents, carefully extract and organize:

- Project objective
- Part A requirements
- Part B requirements
- Part C requirements
- Data contracts
- Scheduling entities
- Scheduling business rules
- API requirements
- Device simulator requirements
- ML forecasting requirements
- Controller requirements
- Command validation requirements
- UI requirements
- Required deliverables
- Optional extensions
- Important constraints
- Required demo behavior
- README requirements
- PROMPTS.md requirements

Pay special attention to exact wording and numerical constraints.

Do not lose details such as:

- Equipment:
  1.5L, 15L, 20L, 75L, 1500L

- Unit operation types:
  Seed, Bioreactor, TFF, Spray, Sum

- Unit operation statuses:
  draft, confirmed, completed

- End dates are exclusive

- Batch containment rule

- Process ordering rule

- Equipment double-booking rule

- Explicit dependency rule

- Completed operation immutability

- Violation reporting behavior

- Required seed data

- Gantt requirements

- Process time vs wall-clock time

- One reading per second in simulator

- 10-minute DO forecast

- 1-minute forecast resolution

- 60-minute input history

- Persistence baseline

- Held-out evaluation

- 5-minute actuator lag

- Feed rate bounds:
  0.0–30.0 mL/h

- Device response model:
  tau = 5 process-minutes
  gain = 2.0 %DO per mL/h

- Command validation rules

- Rejected command persistence

- Live page requirements

- Hosting requirement

- Maximum 3-minute demo

- README requirements

- PROMPTS.md requirements

Optional extensions must remain OPTIONAL.

Do NOT accidentally turn optional extensions into mandatory requirements.

==================================================
STEP 2 — CREATE 01-PROJECT_SPEC.md
==================================================

Create a complete project specification.

It should include:

# Project Specification

## 1. Purpose

## 2. Problem Statement

## 3. Project Goals

## 4. Assignment Scope

## 5. Part A — Scheduling Backend

## 6. Part B — Scheduler UI

## 7. Part C — Closed-Loop Bioreactor Control

## 8. Required Technologies

Separate:
- assignment recommendations
- our selected implementation choices

## 9. Required APIs

## 10. Required Deliverables

## 11. Optional Extensions

## 12. Explicit Non-Goals

## 13. Acceptance Criteria

Do not invent functionality that isn't needed.

==================================================
STEP 3 — CREATE 02-ARCHITECTURE.md
==================================================

Design a clean architecture for the complete application.

The architecture should cover:

Frontend
Backend API
Application/service layer
Database
Scheduling validation
ML forecasting
Controller
Device simulator
Data ingestion
Live control
Testing
Deployment

Prefer a modular architecture.

Clearly define responsibilities and boundaries.

The backend must be the authoritative source for business rules.

The frontend must NOT be treated as the source of truth for scheduling validation.

Document the major request/data flows.

Include diagrams using Mermaid where useful.

At minimum document these flows:

1. Schedule retrieval
2. Create/update unit operation
3. Scheduling validation
4. Device reading ingestion
5. Forecast generation
6. Controller command generation
7. Command validation
8. Device response
9. Live dashboard update

Do not over-engineer the architecture.

The assignment is a proof of concept.

==================================================
STEP 4 — CREATE 03-DOMAIN_RULES.md
==================================================

Document the scheduling domain rules precisely.

Create stable rule IDs.

For example:

DR-001
DR-002
DR-003

etc.

Document:

- Batch containment
- Process ordering
- Equipment overlap
- Explicit dependencies
- Completed operation immutability
- Violation reporting

For every rule include:

- Rule ID
- Name
- Description
- Preconditions
- Validation logic
- Example valid case
- Example invalid case
- Expected violation message
- Operations involved

Pay particular attention to exclusive end dates.

Clearly define interval behavior.

For example:

Operation A:
Oct 1 → Oct 4

Operation B:
Oct 4 → Oct 6

must NOT be considered overlapping.

Also document that a later process type cannot start before every earlier process type in the same batch has ended.

Document that violations should be reported once per violating pair per rule.

==================================================
STEP 5 — CREATE 04-DATABASE_DESIGN.md
==================================================

Design the relational database.

At minimum cover:

Equipment
Batch
UnitOperation
UnitOperationDependency
Reading
Prediction
ControlCommand

For every table document:

- Purpose
- Columns
- Data types
- Primary key
- Foreign keys
- Nullable/non-nullable
- Constraints
- Indexes
- Relationships
- Important invariants

Also document:

- timestamps
- process time
- wall-clock time
- prediction history
- rejected commands
- command status

Do not overwrite historical predictions.

Make the schema consistent with the assignment.

Do not add unnecessary entities unless there is a clear architectural reason.

==================================================
STEP 6 — CREATE 05-API_CONTRACT.md
==================================================

Define the backend API contracts before implementation.

At minimum include:

GET /api/schedule
POST /api/unit_operations
PUT /api/unit_operations/{op_id}
DELETE /api/unit_operations/{op_id}

POST /ingest
POST /command

For every endpoint document:

- Purpose
- HTTP method
- Path
- Query parameters
- Request body
- Response body
- HTTP status codes
- Validation errors
- Example request
- Example response

Use consistent API response structures.

Clearly distinguish:

- validation error
- not found
- conflict
- invalid command
- internal error

Do not invent endpoints unless necessary.

If additional endpoints are needed later, document them as implementation extensions.

==================================================
STEP 7 — CREATE 06-ML_CONTROL_SPEC.md
==================================================

This document must define the entire Part C architecture.

Sections:

## 1. Data

## 2. Process Time

## 3. Device Simulator

## 4. Data Ingestion

## 5. Forecasting

## 6. Baseline

## 7. Evaluation

## 8. Controller

## 9. Command Validation

## 10. Closed-Loop Execution

## 11. Prediction Storage

## 12. Failure and Missing-Data Behavior

Document exactly:

Inputs:
- last 60 minutes of DO
- last 60 minutes of feed rate

Output:
- next 10 minutes
- 1-minute resolution

Baseline:
- persistence / repeat last observed DO

The model may be:
- GRU
- LSTM
- linear
- gradient boosting
- or another justified approach

Do NOT prematurely force a complex model.

Design the architecture so the forecasting implementation can be changed without affecting the rest of the control system.

Document:

- train/validation/test split strategy
- evaluation metric
- baseline comparison
- model persistence
- prediction timestamps
- stale/missing forecast behavior

For the simulator document:

- configurable replay speed
- process time
- wall-clock time
- feed response
- DO response
- actuator lag
- device equations/response model

For controller:

- feed limits
- dwell time
- actuator lag
- command scheduling
- command validation
- rejected command storage

==================================================
STEP 8 — CREATE 07-FRONTEND_SPEC.md
==================================================

Define the UI requirements.

At minimum document:

# Schedule Page

- equipment lanes
- date axis
- scrollable date range
- operation blocks
- colors
- batch grouping
- operation editing modal/drawer
- violation highlighting
- violation messages
- status editing

# Control Page

- DO chart
- feed rate chart
- latest forecast
- command markers
- manual feed setpoint
- rejected commands
- current process time
- current simulator state
- connection/loading/error states

Define the frontend's relationship with backend validation.

Do not duplicate authoritative business logic in React.

Use diagrams/wireframes where useful.

Keep the UI desktop-focused because the assignment explicitly states desktop only.

==================================================
STEP 9 — CREATE 08-IMPLEMENTATION_PLAN.md
==================================================

Create a phased implementation plan.

Use this general order:

Phase 0 — Project foundation
Phase 1 — Database and migrations
Phase 2 — Scheduling domain/backend
Phase 3 — Scheduling validation
Phase 4 — Scheduling APIs
Phase 5 — Gantt scheduler UI
Phase 6 — Device simulator
Phase 7 — Ingestion and persistence
Phase 8 — ML forecasting
Phase 9 — Controller
Phase 10 — Live control UI
Phase 11 — End-to-end integration
Phase 12 — Automated testing
Phase 13 — Deployment
Phase 14 — Documentation and demo

For every phase define:

- Objective
- Tasks
- Files/modules expected
- Dependencies
- Acceptance criteria
- Tests required
- Definition of done

The plan must explicitly state:

DO NOT implement optional extensions until all mandatory requirements are complete and tested.

==================================================
STEP 10 — CREATE 09-DECISIONS.md
==================================================

Create an Architecture Decision Record log.

Initially include only decisions that are actually justified.

Potential decisions to document:

- backend architecture
- database choice
- frontend technology
- API style
- scheduling validation location
- ML model selection strategy
- process-time representation
- simulator architecture
- error handling strategy
- deployment approach

For decisions that have not yet been finalized, mark them:

Status: OPEN

Do not pretend a decision has been made when it hasn't.

Use:

Decision
Context
Options
Chosen approach
Reason
Trade-offs
Status

==================================================
STEP 11 — CREATE REQUIREMENTS_CHECKLIST.md
==================================================

Create a complete traceability checklist.

Every mandatory assignment requirement must appear as a checkbox.

Organize by:

Part A
Part B
Part C
Data/contracts
Submission
Documentation

Each item should have:

- Requirement ID
- Requirement
- Source/section
- Status

Initial status:

NOT STARTED

Do not mark anything complete merely because documentation exists.

Also include optional extensions separately.

==================================================
STEP 12 — CREATE CURSOR RULES
==================================================

Create:

.cursor/rules/00-project-rules.mdc
.cursor/rules/01-architecture-rules.mdc
.cursor/rules/02-backend-rules.mdc
.cursor/rules/03-frontend-rules.mdc
.cursor/rules/04-ml-control-rules.mdc

These rules must guide future Cursor coding sessions.

------------------------------
00-project-rules.mdc
------------------------------

Include:

- assignment PDF is source of truth
- do not invent requirements
- inspect relevant docs before coding
- follow implementation phases
- do not implement optional features prematurely
- don't modify architecture casually
- don't silently change API contracts
- don't silently change database schema
- update documentation when architectural decisions change
- write tests for business-critical logic
- explain changes before implementation
- report files changed
- report tests executed
- report remaining issues

------------------------------
01-architecture-rules.mdc
------------------------------

Define:

- layer boundaries
- module responsibilities
- dependency direction
- backend as source of truth
- separation of scheduling/control/ML concerns
- no unnecessary coupling
- no unnecessary microservices
- simple architecture preferred

------------------------------
02-backend-rules.mdc
------------------------------

Define:

- FastAPI conventions
- Pydantic conventions
- SQLAlchemy conventions
- Alembic migrations
- service layer
- repository/data access
- error handling
- validation
- testing
- business logic placement

Most importantly:

Scheduling rules MUST be enforced server-side.

------------------------------
03-frontend-rules.mdc
------------------------------

Define:

- TypeScript
- component structure
- API client separation
- state management approach
- error/loading states
- no authoritative business rules in frontend
- backend validation is authoritative
- accessibility where practical
- desktop-first behavior

------------------------------
04-ml-control-rules.mdc
------------------------------

Define:

- process time vs wall-clock time
- historical prediction preservation
- reproducible model evaluation
- baseline comparison
- held-out evaluation
- simulator isolation
- controller safety constraints
- feed bounds
- actuator lag
- dwell time
- command validation
- rejected command persistence
- stale forecast handling

==================================================
STEP 13 — CREATE README.md
==================================================

Create an initial README skeleton only.

Include sections:

# BBP Bioprocess Scheduling and Closed-Loop Control

## Overview
## Problem
## Architecture
## Features
## Tech Stack
## Project Structure
## Local Development
## Environment Variables
## Database Setup
## Running the Application
## Scheduling Rules
## ML Forecasting
## Closed-Loop Control
## Seed Data
## Deliberate Violations
## How I split and evaluated the forecaster
## Decisions and trade-offs
## How I would deploy, retrain and monitor this
## Hosted Application
## Demo Video
## AI Usage

Do not fabricate URLs or results.

Use TODO placeholders where information is not available yet.

==================================================
STEP 14 — CREATE PROMPTS.md
==================================================

Create the file required by the assignment.

Because this project will use AI/Cursor, maintain a chronological record.

Use this structure:

# AI Prompts

## Prompt 001 — Project Documentation Bootstrap

Tool:
Cursor

Model:
TODO

Date:
TODO

Purpose:
Create project specification and engineering governance files.

Prompt:
TODO — preserve the exact prompt used.

Changes made by AI:
TODO

Changes reviewed/modified by developer:
TODO

Issues found:
TODO

For future prompts, append them in chronological order.

IMPORTANT:
Do not fabricate future prompts.

==================================================
STEP 15 — REVIEW THE CREATED DOCUMENTS
==================================================

After creating all files, perform a consistency review.

Check:

1. Does every assignment requirement appear somewhere?
2. Are all scheduling rules represented consistently?
3. Are API contracts consistent with the domain model?
4. Is the database design consistent with the API?
5. Is the ML design consistent with the assignment?
6. Is process time clearly separated from wall-clock time?
7. Are controller constraints represented?
8. Are frontend requirements represented?
9. Are required deliverables represented?
10. Are optional extensions clearly separated?
11. Are there contradictions between documents?
12. Did we accidentally invent requirements?
13. Are there any missing acceptance criteria?

If you find contradictions, fix the documentation before finishing.

==================================================
CRITICAL CONSTRAINTS
==================================================

DO NOT:

- build application code
- create React components
- create FastAPI routes
- create database migrations
- train ML models
- create the simulator implementation
- implement optional extensions
- invent business rules
- invent evaluation results
- claim tests pass
- claim deployment exists
- fabricate data

This task is documentation and project governance ONLY.

==================================================
FINAL OUTPUT
==================================================

After completing the work, provide a concise summary containing:

1. Files created
2. Key architectural decisions
3. Any open decisions
4. Any assumptions explicitly marked as design choices
5. Any ambiguities found in the assignment
6. Confirmation that no application implementation was created

Do not start implementation until I explicitly ask you to begin Phase 0.
```

**Changes made by AI:**  

- Created `bbp-scheduling/docs/01-PROJECT_SPEC.md` through `09-DECISIONS.md`
- Created `bbp-scheduling/.cursor/rules/00-project-rules.mdc` through `04-ml-control-rules.mdc`
- Created `bbp-scheduling/README.md`, `REQUIREMENTS_CHECKLIST.md`, `PROMPTS.md`
- Analyzed `Take_Home_SWE_ML_Brief.pdf` and `data_kit/` (`run_A/B/C.csv`, `limits.json`, README)

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO — see session summary: ADR-005 save policy, dwell duration unspecified, batch end-date exclusivity, multiple ops of same type

---

## Prompt 002 — Phase 0 Project Foundation

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Scaffold `backend/`, `frontend/`, `simulator/`, copy `data_kit`, add `.env.example`, smoke health endpoints; no business logic.

**Prompt:**  

```text
yes start with phase 0
```

**Changes made by AI:**  

- Created FastAPI app with `GET /api/health`, settings, package layout
- Created Vite React+TS frontend with health status page + API proxy
- Created simulator scaffold (`python -m bbp_simulator --hello`)
- Copied `data_kit/` into repo; added `.env.example`, `.gitignore`, `scripts/smoke.ps1`
- Updated root `README.md` with local run instructions

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 003 — Phase 1 Database and Migrations

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Implement SQLModel schema, Alembic initial migration, equipment seed, migration smoke tests.

**Prompt:**  

```text
Phase 1
```

**Changes made by AI:**  

- Added scheduling + control ORM models per `04-DATABASE_DESIGN.md`
- Alembic `initial_schema` migration; `python -m app.db.bootstrap`
- Seeded five equipment rows; tests for upgrade/downgrade/seed/uniqueness
- Recorded ADR-013 (ON DELETE RESTRICT)

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 004 — Phase 2 Scheduling Domain and Seed

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Add scheduling repositories/service and seed ≥3 batches with ≥2 deliberate violations; verify re-run bootstrap first.

**Prompt:**  

```text
i run again "python -m app.db.bootstrap" chek it and if every thing good start phase 2
```

**Changes made by AI:**  

- Verified idempotent equipment bootstrap
- Added `repositories/scheduling.py`, `services/scheduling.py`
- Seeded Batch Alpha/Bravo/Charlie with DR-002 and DR-003 deliberate violations
- Wired schedule seed into `app.db.bootstrap`; repository/seed tests
- Documented seed + violations in README

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 005 — Phase 3 Scheduling Validation

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Implement DR-001–DR-005 with exclusive end dates, pair dedupe, and tests.

**Prompt:**  

```text
Phase 3
```

**Changes made by AI:**  

- Added `app/domain/scheduling_rules.py` (overlap, DR-001–DR-005, evaluate_schedule)
- Wired `evaluate_violations` + DR-005 enforcement into `SchedulingService`
- Unit + integration tests (seed deliberate violations detected)
- ADR-014 for completed-op update policy

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 006 — Phase 4 Scheduling APIs

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Expose GET /api/schedule and unit operation POST/PUT/DELETE with ADR-005 policy and error envelope.

**Prompt:**  

```text
phase 4
```

**Changes made by AI:**  

- Implemented schedule + unit_operations routes and Pydantic schemas
- Locked ADR-005 Option B (save-and-return); DR-005 still 409
- Unified JSON error envelope handlers
- API integration tests (40 total tests passing)

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 007 — Phase 5 Gantt Scheduler UI

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Build desktop Schedule Gantt UI consuming Part A APIs (lanes, envelopes, edit drawer, violation highlight).

**Prompt:**  

```text
start phase 5
```

**Changes made by AI:**  

- Custom Gantt (ADR-006): equipment lanes, date axis, batch envelopes, violation borders
- Edit drawer for start/end/equipment/status; violations panel
- react-router Schedule + Control placeholder
- Frontend production build verified

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 008 — Phase 6 Device Simulator

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Implement fermentation run replay, feed/DO response model, 1 Hz emit, dry-run CLI.

**Prompt:**  

```text
lets move to next step
```

**Changes made by AI:**  

- `bbp_simulator` CSV loader, response model (τ=5, g=2.0, clamp), device loop
- CLI dry-run with optional local feed command; tests (6 passed)
- Docs/checklist updates; ingest POST gated behind `--post-ingest` (Phase 7)

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 009 — Phase 7 Ingest and Persistence

**Tool:**  
Cursor

**Model:**  
TODO

**Date:**  
2026-09-29

**Purpose:**  
Implement POST /ingest, reading persistence, process-time tracking, GET /api/control/state.

**Prompt:**  

```text
Phase 7
```

**Changes made by AI:**  

- Ingest service/repo + POST /ingest
- GET /api/control/state extension
- API tests; simulator `--post-ingest` now usable

**Changes reviewed/modified by developer:**  
TODO

**Issues found:**  
TODO

---

## Prompt 010 —

*(Append next prompts below in chronological order. Do not fabricate future prompts.)*
