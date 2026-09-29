# API Contract

**Document ID:** `05-API_CONTRACT`  
**Style:** REST JSON  
**Authority:** This contract must not change silently; update docs before code  

---

## 1. Conventions

### 1.1 Base URL

Design Decision / Implementation Choice — e.g. `http://localhost:8000`.

### 1.2 Dates

Schedule dates: ISO `YYYY-MM-DD`. End dates exclusive per domain rules.

### 1.3 Process time

`time_h` / `apply_at_time_h`: float hours from inoculation.

### 1.4 Error envelope

```json
{
  "error": {
    "code": "validation_error | not_found | conflict | invalid_command | internal_error",
    "message": "Human-readable summary",
    "details": []
  }
}
```

`details` may include violation objects for scheduling:

```json
{
  "rule_id": "DR-003",
  "message": "Equipment \"1.5L\" double-booked by \"Op A\" and \"Op B\".",
  "operation_ids": [1, 2]
}
```

### 1.5 HTTP status mapping

| Situation | Status | `error.code` |
|-----------|--------|--------------|
| Request body/query invalid | 422 | `validation_error` |
| Business rule reject (if reject policy) | 409 or 422 | `conflict` or `validation_error` — **ADR-005** |
| Resource missing | 404 | `not_found` |
| Invalid control command | 400 or 422 | `invalid_command` |
| Unhandled server failure | 500 | `internal_error` |

---

## 2. Scheduling Endpoints

### 2.1 GET `/api/schedule`

| Field | Value |
|-------|--------|
| **Purpose** | All data needed for the Gantt grid in a date range, including current violations |
| **Method** | GET |
| **Path** | `/api/schedule` |
| **Query** | `start_date` (required), `end_date` (required) — ISO dates |

**Request body:** none  

**Response 200:**

```json
{
  "start_date": "2025-10-01",
  "end_date": "2025-11-30",
  "equipment": [
    { "id": 1, "name": "1.5L" }
  ],
  "batches": [
    {
      "id": 1,
      "name": "Batch A",
      "start_date": "2025-10-01",
      "end_date": "2025-11-01"
    }
  ],
  "unit_operations": [
    {
      "id": 10,
      "name": "Seed A",
      "type": "Seed",
      "color": "#4C9F70",
      "status": "confirmed",
      "start_date": "2025-10-05",
      "end_date": "2025-10-08",
      "batch_id": 1,
      "equipment_id": 1
    }
  ],
  "dependencies": [
    { "id": 1, "from_unitop_id": 10, "to_unitop_id": 11 }
  ],
  "violations": [
    {
      "rule_id": "DR-003",
      "message": "Equipment \"1.5L\" double-booked by \"Seed A\" and \"Seed B\".",
      "operation_ids": [10, 12]
    }
  ]
}
```

**Errors:** 422 invalid/missing dates; 500 internal  

**Notes:** Include ops that intersect `[start_date, end_date)`. Exact intersection rule for batches/deps: Design Decision / Implementation Choice — prefer include batch if any op intersects.

---

### 2.2 POST `/api/unit_operations`

| Field | Value |
|-------|--------|
| **Purpose** | Create a unit operation |
| **Method** | POST |
| **Path** | `/api/unit_operations` |

**Request body:**

```json
{
  "name": "Bioreactor A",
  "type": "Bioreactor",
  "color": "#2F6FED",
  "status": "draft",
  "start_date": "2025-10-08",
  "end_date": "2025-10-15",
  "batch_id": 1,
  "equipment_id": 2
}
```

**Response — reject policy (ADR-005 Option A):**

- `201` created with body `{ "unit_operation": {...}, "violations": [] }` when valid  
- `409`/`422` with error envelope + violation details when invalid; **not** persisted  

**Response — save-and-return policy (ADR-005 Option B):**

- `201` with `{ "unit_operation": {...}, "violations": [ ... ] }` even if violations non-empty  

**Errors:** 404 batch/equipment not found; 422 schema; 500  

---

### 2.3 PUT `/api/unit_operations/{op_id}`

| Field | Value |
|-------|--------|
| **Purpose** | Update a unit operation (dates, equipment, status, name, color, type as allowed) |
| **Method** | PUT |
| **Path** | `/api/unit_operations/{op_id}` |
| **Path params** | `op_id` integer |

**Request body:** same fields as create (full replace) or documented subset — Design Decision / Implementation Choice: full PUT vs partial; prefer full resource replace for clarity.

**Example request:**

```json
{
  "name": "Bioreactor A",
  "type": "Bioreactor",
  "color": "#2F6FED",
  "status": "confirmed",
  "start_date": "2025-10-09",
  "end_date": "2025-10-16",
  "batch_id": 1,
  "equipment_id": 2
}
```

**Response:** same policy as POST (`200` + entity + violations, or error without silent success)  

**Errors:** 404 not found; DR-005 → conflict/validation; 422; 500  

---

### 2.4 DELETE `/api/unit_operations/{op_id}`

| Field | Value |
|-------|--------|
| **Purpose** | Delete a unit operation |
| **Method** | DELETE |
| **Path** | `/api/unit_operations/{op_id}` |

**Request body:** none  

**Response 204:** empty on success  

**Errors:** 404; 409/422 if `completed` (DR-005); 500  

---

## 3. Control Endpoints (assignment)

### 3.1 POST `/ingest`

| Field | Value |
|-------|--------|
| **Purpose** | Receive pushed device readings and persist them |
| **Method** | POST |
| **Path** | `/ingest` |

**Request body:**

```json
{
  "readings": [
    { "time_h": 12.350, "signal_name": "DO", "value": 38.2, "unit": "%" },
    { "time_h": 12.350, "signal_name": "feed_rate", "value": 5.0, "unit": "mL/h" }
  ]
}
```

**Response 200:**

```json
{
  "accepted": 2,
  "current_process_time_h": 12.350
}
```

Response shape beyond acceptance is Design Decision / Implementation Choice; must persist readings.

**Errors:** 422 invalid payload; 500  

---

### 3.2 POST `/command`

| Field | Value |
|-------|--------|
| **Purpose** | Submit a feed (or other) setpoint command for validation and storage |
| **Method** | POST |
| **Path** | `/command` |

**Request body:**

```json
{
  "setpoint_name": "feed_rate",
  "value": 8.0,
  "unit": "mL/h",
  "apply_at_time_h": 12.400
}
```

**Response 200 (accepted):**

```json
{
  "id": 41,
  "setpoint_name": "feed_rate",
  "value": 8.0,
  "unit": "mL/h",
  "apply_at_time_h": 12.400,
  "status": "pending",
  "source": "manual"
}
```

**Response 400/422 (rejected — still persisted):**

```json
{
  "error": {
    "code": "invalid_command",
    "message": "value outside bounds",
    "details": [
      {
        "command_id": 42,
        "status": "rejected",
        "reject_reason": "value 35.0 outside [0.0, 30.0] mL/h"
      }
    ]
  }
}
```

Assignment requires reject with reason **and** store rejected commands. HTTP may be 4xx while DB retains the row.

**Validation failure reasons (minimum):**

1. Value outside bounds  
2. `apply_at_time_h` earlier than device current process time  
3. Unit does not match expected unit for setpoint  
4. Another command for the same setpoint still pending  

---

## 4. Implementation Extension Endpoints

Not required by the assignment PDF. Document here before implementing. Suggested for Live page polling:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/control/state` | Recent readings, commands, current process time |
| POST | `/api/control/step` | One reactive controller evaluation |
| GET | `/api/control/commands/pending` | Pending setpoints for device poll |
| POST | `/api/control/commands/{id}/ack` | Device marks command applied |
| POST | `/api/forecast` | Generate append-only DO forecast |
| GET | `/api/forecast/latest` | Latest forecast points |
| GET | `/api/health` | Liveness |

`GET /api/control/state` is implemented as a Phase 7 debugging/live-prep extension.

---

## 5. Example: schedule violation highlight flow

1. UI `GET /api/schedule?start_date=2025-10-01&end_date=2025-11-30`  
2. Response includes `violations[].operation_ids`  
3. UI highlights those ops; shows `message` on hover/list  
4. User edits via PUT; response shows cleared or remaining violations  

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial contract from assignment paths |
| 0.2 | 2026-09-29 | ADR-005 Option B chosen; full PUT; health at GET /api/health |
