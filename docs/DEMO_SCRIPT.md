# Demo Script (≤3 minutes)

Timed walkthrough for screen recording / live demo.  
Assumes local stack is already running (see **Cold start** below if not).

**Target:** Schedule violations + edit clear + closed control loop.

---

## Cold start (before recording — not in the 3 minutes)

```powershell
# Terminal 1 — backend
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.db.bootstrap
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev

# Terminal 3 — seed ~70 process-minutes for forecast (one-shot)
cd simulator
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --max-ticks 70 --no-sleep --post-ingest
```

Optional continuous closed loop (leave running during Control segment):

```powershell
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --start-time-h 1.1667 --max-ticks 30 --post-ingest --poll-commands --no-sleep
```

Or use `.\scripts\demo-prep.ps1` from repo root (bootstrap + 70-tick ingest).

---

## Minute 0:00–0:45 — Schedule: violations highlighted

1. Open http://127.0.0.1:5173/
2. Date range ~ **2025-10-01 → 2025-11-15** (defaults).
3. Point out red / highlighted blocks and the violations list:
   - **DR-003:** `Bravo Bioreactor 1.5L` + `Charlie Seed 1.5L` (same `1.5L`, overlap)
   - **DR-002:** `Charlie Seed 75L` + `Charlie Bioreactor 1500L` (Bioreactor starts before Seed ends)

---

## Minute 0:45–1:30 — Schedule: edit clears a violation

1. Click **Charlie Bioreactor 1500L**.
2. Change **start date** from `2025-10-23` to **`2025-10-24`** (or later).
3. Save — DR-002 should clear (or drop from the list).
4. Optionally note DR-003 remains until one of the overlapping `1.5L` ops is moved.

---

## Minute 1:30–3:00 — Control loop

1. Open http://127.0.0.1:5173/control
2. Show **process time**, DO ~99%, feed trace, **forecast** dashed overlay (needs ≥60 min history).
3. Click **Run controller step** → pending feed command (apply_at = now + 5 min lag).
4. Or **Send** a manual setpoint (e.g. `8.0`).
5. If simulator is running with `--poll-commands`, show feed responding and DO `dDO` moving after apply time.
6. Optionally send `35` to show **rejected** command in the list.

---

## Recording checklist

- [ ] Gantt with ≥1 violation visible
- [ ] Edit that clears a violation
- [ ] Control: readings + forecast + command marker / reject
- [ ] Keep total ≤ 3:00

Place the file under `docs/demo/` or link from README **Demo Video** when recorded.
