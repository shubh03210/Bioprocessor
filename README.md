# BBP Bioprocess Scheduling and Closed-Loop Control

Proof-of-concept for Boston Bioprocess: rule-enforcing batch/unit-operation **Schedule**, plus a single-vessel **closed-loop control** demo (readings → forecast → feed command → live UI).

**Repo:** https://github.com/shubh03210/Bioprocessor  
**Status:** Live on Render. Remaining: demo video, PROMPTS polish, GitHub invites.

---

## Quick start (Windows / PowerShell)

**Prerequisites:** Python **3.11+**, Node.js **20+**.

Do these steps **in order**. You need **two terminals** for the UI (backend + frontend).

### 1. Clone

```powershell
git clone https://github.com/shubh03210/Bioprocessor.git
cd Bioprocessor
```

### 2. Backend — install, seed DB, start API

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.bootstrap
uvicorn app.main:app --reload --port 8000
```

Leave this running. Check: http://127.0.0.1:8000/api/health  

`bootstrap` creates SQLite `bbp.db`, equipment, and the demo schedule (with deliberate violations).  
Trained forecaster is already in `app/ml/artifacts/` — no retrain needed.

### 3. Frontend — install and start UI (new terminal)

```powershell
cd Bioprocessor\frontend
npm install
npm run dev
```

Open:

| Page | URL |
|------|-----|
| **Schedule** (Gantt + violations) | http://127.0.0.1:5173/ |
| **Live Control** | http://127.0.0.1:5173/control |

Vite proxies `/api`, `/ingest`, and `/command` to the backend on port 8000.

### 4. (Optional) Fill Control page with readings

With the **backend still running**, from the **repo root**:

```powershell
cd Bioprocessor
.\scripts\demo-prep.ps1
```

Or manually:

```powershell
cd simulator
pip install -e .
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --max-ticks 70 --no-sleep --post-ingest
```

Then refresh **Control** — DO/feed traces + forecast overlay (≥60 process-minutes).

### 5. (Optional) Closed loop — device polls commands

```powershell
cd simulator
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --start-time-h 1.1667 --max-ticks 40 --no-sleep --post-ingest --poll-commands
```

On the Control page: **Run controller step** or **Send** a setpoint; the simulator applies feed when process time reaches `apply_at`.

---

## What you should see

1. **Schedule** — equipment lanes, batches, red/highlighted **DR-002** and **DR-003** violations.
2. Edit **Charlie Bioreactor 1500L** start → `2025-10-24` → DR-002 with Seed 75L clears.
3. **Control** (after step 4) — process time, DO/feed charts, forecast dashed line, command markers.

Full recording script: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## Verify install (optional)

Backend must be running for the API check.

```powershell
# From repo root, with backend venv available for pytest:
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest

cd ..\simulator
$env:PYTHONPATH = "."
python -m pytest

cd ..
.\scripts\e2e-check.ps1
.\scripts\smoke.ps1
```

---

## Environment (optional)

Defaults work without a `.env`. To customize:

```powershell
copy .env.example backend\.env
```

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Default `sqlite:///./bbp.db` |
| `CORS_ORIGINS` | Default allows Vite on `5173` |
| `FEED_RATE_MIN` / `FEED_RATE_MAX` | `0`–`30` mL/h |
| `ACTUATOR_LAG_PROCESS_MINUTES` | `5` |
| `CONTROLLER_DWELL_PROCESS_MINUTES` | `5` |
| `VITE_API_BASE` | Leave empty to use Vite proxy |

---

## Project layout

```text
Bioprocessor/
  backend/       FastAPI + SQLite + ML artifact
  frontend/      React + Vite (Schedule + Control)
  simulator/     Device replay + response model
  data_kit/      run_A/B/C.csv, limits.json
  docs/          Specs + DEMO_SCRIPT.md
  scripts/       demo-prep.ps1, e2e-check.ps1, smoke.ps1
```

Architecture: [`docs/02-ARCHITECTURE.md`](docs/02-ARCHITECTURE.md).

---

## Scheduling rules

[`docs/03-DOMAIN_RULES.md`](docs/03-DOMAIN_RULES.md) — DR-001–DR-005; exclusive end dates `[start, end)`.

**Save policy (ADR-005 Option B):** create/update **save-and-return** violations. DR-005 (completed ops) still **409**.

### Seed data (after bootstrap)

| Batch | Role |
|-------|------|
| Batch Alpha | Valid schedule (Seed → Bioreactor + dependency) |
| Batch Bravo | DR-003 participant |
| Batch Charlie | DR-002 + DR-003 participants |

### Deliberate violations

| Rule | Operations | Detail |
|------|------------|--------|
| DR-003 | `Bravo Bioreactor 1.5L` + `Charlie Seed 1.5L` | Same `1.5L`, overlap Oct 29–30 |
| DR-002 | `Charlie Seed 75L` + `Charlie Bioreactor 1500L` | Bioreactor starts before Seed ends |

---

## How I split and evaluated the forecaster

**Task:** last **60** min DO + feed → next **10** min DO (1-min steps).

**Split:** train `run_A` + `run_B`; hold out `run_C`.

**Baseline:** persistence (repeat last DO).

**Model:** Ridge multi-output linear (`ridge-linear-v1`) — shipped under `backend/app/ml/artifacts/`.

| Model (hold-out run_C) | MAE (%DO) | RMSE (%DO) |
|------------------------|-----------|------------|
| Ridge linear | **0.498** | **0.898** |
| Persistence baseline | 0.576 | 1.062 |

Optional retrain: `cd backend && python -m app.ml.train`.

---

## Closed-loop control (summary)

See [`docs/06-ML_CONTROL_SPEC.md`](docs/06-ML_CONTROL_SPEC.md).

- Feed bounds `0`–`30` mL/h; lag **5** process-minutes; dwell **5** process-minutes
- Device response: τ=5, g=2.0; DO clamped `[0, 100]`
- APIs: `POST /ingest`, `POST /command`, `POST /api/control/step`, `GET /api/control/commands/pending`

---

## Decisions and trade-offs

See [`docs/09-DECISIONS.md`](docs/09-DECISIONS.md). Highlights:

1. **ADR-005** — save-and-return violations (except hard DR-005 reject).
2. **ADR-006** — custom Gantt (not a paid timeline library).
3. **ADR-007** — Ridge linear over persistence / deep models for the PoC.

---

## How I would deploy, retrain and monitor this

**Deploy (no Docker):** one web service builds the Vite SPA into `backend/app/static` and runs uvicorn (see **Hosting** below / ADR-008). On start: migrate + seed schedule + seed ~70 min of `run_A` readings so Control has history without a live simulator.

**Retrain:** offline `python -m app.ml.train` on new runs; commit or release the `.joblib` artifact; restart service. Prefer versioned `model_version` on prediction rows.

**Monitor:** health `/api/health`; log ingest accept counts, command reject reasons, forecast skip (insufficient history); alert on 5xx and bootstrap failure. Free-tier sleep is acceptable for a take-home demo.

## Hosting (Phase 13)

Packaging is in-repo (`render.yaml`, `scripts/render-build.sh`, `scripts/render-start.sh`). **No Docker.**  
The production UI is the committed build in `backend/app/static` (rebuild with `.\scripts\build-static.ps1` after frontend changes).

### Option A — Render (recommended)

1. Go to [Render](https://render.com) → **New** → **Blueprint** (or **Web Service**) and connect https://github.com/shubh03210/Bioprocessor  
2. If manual Web Service:
   - **Root directory:** (repo root)
   - **Build:** `bash scripts/render-build.sh`
   - **Start:** `bash scripts/render-start.sh`
   - **Health:** `/api/health`
3. After deploy, open the public URL — Schedule + Control on the **same origin**.
4. Paste that URL into **Hosted Application** below.
### Option B — Local production check

```powershell
.\scripts\run-prod-local.ps1
```

Opens http://127.0.0.1:8000/ (API + built UI together).

### Hosted Application

**Live URL:** https://bioprocessor.onrender.com  

- Schedule: https://bioprocessor.onrender.com/  
- Control: https://bioprocessor.onrender.com/control  

Free tier may cold-start slowly after idle (~30–60s).
## Demo Video

TODO — ≤3 minute recording (see [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)).

## AI Usage

See [`PROMPTS.md`](PROMPTS.md).

## Checklist

[`REQUIREMENTS_CHECKLIST.md`](REQUIREMENTS_CHECKLIST.md) traces assignment requirements.
