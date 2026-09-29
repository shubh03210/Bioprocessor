# BBP Backend

## Phase 0

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: `GET http://localhost:8000/api/health`

## Phase 1 — Database

```powershell
python -m app.db.bootstrap
# or: alembic upgrade head
pytest -q
```

Creates SQLite `bbp.db` (by default) with all Part A/C tables, seeds equipment, and loads the demo schedule.

## Phase 4 — Scheduling APIs

With the API running (`uvicorn app.main:app --reload --port 8000`):

- `GET /api/schedule?start_date=2025-10-01&end_date=2025-11-30`
- `POST /api/unit_operations`
- `PUT /api/unit_operations/{id}`
- `DELETE /api/unit_operations/{id}`

Violations are returned on GET and on create/update (save-and-return).
