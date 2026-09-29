# BBP Bioprocess Scheduling and Closed-Loop Control

## Overview

Proof-of-concept desktop web application for Boston Bioprocess: a rule-enforcing batch/unit-operation scheduler and a single-vessel closed-loop bioreactor control demo (readings → forecast → feed command → live UI).

**Status:** Phases 0–11 complete locally (schedule + closed-loop demo path). Remaining: automated test hardening (12), hosting (13), submission polish (14).

Primary source of truth: `Take_Home_SWE_ML_Brief.pdf` (parent assignment package).

## Problem

Batches are planned as interdependent unit operations on scarce equipment using spreadsheets that are slow and error-prone. Separately, operators manually adjust feed from DO, which is hard to do consistently in real time. This project replaces both with a single scheduling source of truth and a small closed control loop.

## Architecture

See [`docs/02-ARCHITECTURE.md`](docs/02-ARCHITECTURE.md).

High level: React SPA → FastAPI modular monolith → SQLite/PostgreSQL; separate device simulator process; ML forecaster behind a swappable interface.

## Features

**Mandatory (in progress by phase):**

- Phase 0–4 — Foundation, DB, seed, rules, scheduling APIs (done)
- Phase 5 — Gantt scheduler UI (done)
- Phase 6–9 — Simulator, ingest, forecast, controller/commands (done)
- Phase 10 — Live control UI (done)
- Phase 11 — E2E demo script / integration (done)
- Phase 12 — Automated testing (done)
- Phases 13–14 — Deploy, submission

**Optional (deferred until mandatory complete):** E1–E4 per assignment §5.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Backend | FastAPI, Pydantic, SQLModel/SQLAlchemy, Alembic |
| DB | SQLite (local); PostgreSQL-compatible |
| Frontend | React + TypeScript (Vite) |
| Simulator | Python package (`bbp_simulator`) |
| ML | Ridge multi-output linear (beats persistence; ADR-007) |

## Project Structure

```text
bbp-scheduling/
  .cursor/rules/
  docs/
  backend/           # FastAPI app
  frontend/          # Vite React TS
  simulator/         # Device simulator (scaffold)
  data_kit/          # Provided fermentation runs
  scripts/smoke.ps1
  .env.example
  README.md
  REQUIREMENTS_CHECKLIST.md
  PROMPTS.md
```

## Local Development

Prerequisites: Python 3.11+, Node 20+.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env   # optional
uvicorn app.main:app --reload --port 8000
```

Health: http://127.0.0.1:8000/api/health

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173 — Schedule (`/`) and Live Control (`/control`); proxies `/api`, `/ingest`, `/command` to backend on port 8000.

Keep the backend running (`uvicorn` on 8000) while using the UI.

### Simulator

```powershell
cd simulator
pip install -e .
python -m bbp_simulator --hello
```

### Smoke script

```powershell
.\scripts\smoke.ps1
```

Runs backend pytest, simulator pytest, and frontend production build.

## Testing

### Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Critical coverage: DR-001–005 unit + API, ingest, forecast (baseline + Ridge), all four command reject reasons, controller lag/pending, migrations/seed.

Shared fixtures: `tests/conftest.py` (`api_client`, `seeded_api_client`).

### Simulator

```powershell
cd simulator
$env:PYTHONPATH = "."
python -m pytest
```

Covers response model (τ, g, clamp), device ticks, and API command poll/ack (mocked).

### Frontend

No unit-test runner yet. Regression check:

```powershell
cd frontend
npm run build
```

### Live API smoke (backend up)

```powershell
.\scripts\e2e-check.ps1
```

### Demo prep

```powershell
.\scripts\demo-prep.ps1
```

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

## Environment Variables

See [`.env.example`](.env.example). Important keys:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | DB URL (default SQLite `./bbp.db`) |
| `DATA_KIT_PATH` | Path to run CSVs |
| `CORS_ORIGINS` | Allowed browser origins |
| `FEED_RATE_MIN` / `FEED_RATE_MAX` | Command bounds (0–30) |
| `ACTUATOR_LAG_PROCESS_MINUTES` | 5 process-minutes |
| `CONTROLLER_DWELL_PROCESS_MINUTES` | Design choice default 5 until finalized |
| `VITE_API_BASE` | Optional; leave empty to use Vite proxy |

## Database Setup

From `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
python -m app.db.bootstrap
```

This runs `alembic upgrade head`, seeds equipment (`1.5L`…`1500L`), and loads the demo schedule (3 batches, deliberate DR-002/DR-003 violations) if not already present.

Manual migrate:

```powershell
alembic upgrade head
alembic downgrade base   # tear down (destroys schema)
```

See **Seed Data** / **Deliberate Violations** below.

## Running the Application

1. **Backend** — `uvicorn app.main:app --reload --port 8000` (after `python -m app.db.bootstrap`).
2. **Frontend** — `npm run dev` → http://127.0.0.1:5173/
3. **Demo prep** (readings for Control page):

```powershell
.\scripts\demo-prep.ps1
```

4. **Recording walkthrough:** [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) (≤3 minutes).
5. **API smoke:** `.\scripts\e2e-check.ps1` (backend up).

### Closed-loop simulator (poll commands)

```powershell
cd simulator
$env:PYTHONPATH = "."
# Seed history, then continue with command polling:
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --max-ticks 70 --no-sleep --post-ingest
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --start-time-h 1.1667 --max-ticks 40 --no-sleep --post-ingest --poll-commands
```

With `--poll-commands`, the device picks up `POST /command` / controller setpoints and acks them via `POST /api/control/commands/{id}/ack`.

## Scheduling Rules

Documented in [`docs/03-DOMAIN_RULES.md`](docs/03-DOMAIN_RULES.md) (DR-001–DR-005). End dates are exclusive (`[start, end)`).

Implemented in `backend/app/domain/scheduling_rules.py`. `SchedulingService.evaluate_violations()` returns current violations; DR-005 is enforced on update/delete.

**Save policy on violations:** **ADR-005 Option B (save-and-return)** — create/update persist the operation and return current `violations` in the response. DR-005 (completed immutability) still rejects with HTTP 409.

## ML Forecasting

See **How I split and evaluated the forecaster** below. Artifact: `backend/app/ml/artifacts/ridge-linear-v1.joblib`. Train: `python -m app.ml.train`.

## Closed-Loop Control

See [`docs/06-ML_CONTROL_SPEC.md`](docs/06-ML_CONTROL_SPEC.md). Feed bounds `0.0–30.0` mL/h; actuator lag 5 process-minutes; τ=5, g=2.0 response model.

### Device simulator (Phase 6)

```powershell
cd simulator
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --command-at 0 --command-value 10 --max-ticks 10 --no-sleep
```

Default is dry-run (prints readings). To persist:

```powershell
# backend must be running
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --max-ticks 5 --no-sleep --post-ingest
```

Then inspect: `GET http://127.0.0.1:8000/api/control/state`

## Seed Data

Loaded by `python -m app.db.bootstrap` (idempotent):

| Batch | Role |
|-------|------|
| Batch Alpha | Valid control schedule (Seed 1.5L → Bioreactor 15L + explicit dependency) |
| Batch Bravo | Includes `Bravo Bioreactor 1.5L` (DR-003 participant) |
| Batch Charlie | Includes ordering + double-book participants |

Equipment: `1.5L`, `15L`, `20L`, `75L`, `1500L`.

## Deliberate Violations

| Rule | Operations | Detail |
|------|------------|--------|
| DR-003 | `Bravo Bioreactor 1.5L` + `Charlie Seed 1.5L` | Same equipment `1.5L`, overlap Oct 29–Oct 30 (exclusive ends) |
| DR-002 | `Charlie Seed 75L` + `Charlie Bioreactor 1500L` | Bioreactor starts Oct 23 before Seed ends Oct 24 |

Domain rule evaluation is live on Schedule; seeded rows are the deliberate demo violations.

## How I split and evaluated the forecaster

**Task:** predict next **10** process-minutes of DO from the last **60** minutes of DO + feed_rate (1-min resolution).

**Split (Design Decision):** train on `run_A.csv` + `run_B.csv`; hold out `run_C.csv` entirely.

**Baseline:** persistence — repeat the last observed DO across the 10-minute horizon.

**Model:** Ridge multi-output linear regression (`ridge-linear-v1`) over the concatenated 60-step DO and feed histories. Chosen as the simplest model that beat the baseline (ADR-007).

**Metrics on hold-out `run_C` (2,331 windows):**

| Model | MAE (%DO) | RMSE (%DO) |
|-------|-----------|------------|
| Ridge linear | **0.498** | **0.898** |
| Persistence baseline | 0.576 | 1.062 |

Retrain: `cd backend && python -m app.ml.train` (writes `app/ml/artifacts/ridge-linear-v1.joblib`).  
Live API: `POST /api/forecast` (append-only predictions); `GET /api/forecast/latest`.

## Decisions and trade-offs

See [`docs/09-DECISIONS.md`](docs/09-DECISIONS.md). README will summarize ≥2 trade-offs after implementation (assignment requirement).

## How I would deploy, retrain and monitor this

TODO — after Phase 13/14 design reflection.

## Hosted Application

TODO — URL after deployment. Do not fabricate.

## Demo Video

TODO — ≤3 minute recording link or repo path.

## AI Usage

See [`PROMPTS.md`](PROMPTS.md). AI tools are allowed; prompts are recorded chronologically.
