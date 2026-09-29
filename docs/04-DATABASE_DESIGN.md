# Database Design

**Document ID:** `04-DATABASE_DESIGN`  
**Aligned with:** Assignment entities + Part C persistence minimum  
**Engine:** SQLite locally; PostgreSQL-compatible types/constraints (ADR-002)  

---

## 1. Design Principles

- Relational model matching Part A entities and Part C tables (readings, predictions, control commands).
- Predictions are **append-only** — never update historical prediction rows.
- Rejected commands are **persisted** with reason.
- Separate **process time** (`time_h` / `apply_at_time_h` / `made_at_time_h` as float hours) from **wall-clock** (`created_at` timestamptz/datetime).
- Do not add entities without a clear architectural reason.

---

## 2. Entity-Relationship Overview

```mermaid
erDiagram
  Equipment ||--o{ UnitOperation : hosts
  Batch ||--o{ UnitOperation : contains
  UnitOperation ||--o{ UnitOperationDependency : from
  UnitOperation ||--o{ UnitOperationDependency : to
  Reading }o--|| DeviceContext : optional
  Prediction }o--|| DeviceContext : optional
  ControlCommand }o--|| DeviceContext : optional

  Equipment {
    int id PK
    string name UK
  }
  Batch {
    int id PK
    string name
    date start_date
    date end_date
  }
  UnitOperation {
    int id PK
    string name
    string type
    string color
    string status
    date start_date
    date end_date
    int batch_id FK
    int equipment_id FK
  }
  UnitOperationDependency {
    int id PK
    int from_unitop_id FK
    int to_unitop_id FK
  }
  Reading {
    int id PK
    float time_h
    string signal_name
    float value
    string unit
    datetime created_at
  }
  Prediction {
    int id PK
    float made_at_time_h
    float target_time_h
    string signal_name
    float value
    string unit
    string model_version
    datetime created_at
  }
  ControlCommand {
    int id PK
    string setpoint_name
    float value
    string unit
    float apply_at_time_h
    string status
    string reject_reason
    string source
    datetime created_at
  }
```

`DeviceContext` / `vessel_id` is **not** required for single-vessel PoC.  
**Design Decision / Implementation Choice:** omit until E4; if added early, nullable default vessel `"default"`.

---

## 3. Tables

### 3.1 `equipment`

| Item | Detail |
|------|--------|
| **Purpose** | Catalog of physical vessels/lanes |
| **Primary key** | `id` |
| **Seed** | `1.5L`, `15L`, `20L`, `75L`, `1500L` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK, autoincrement |
| name | VARCHAR(64) | NO | UNIQUE |

**Indexes:** UNIQUE(`name`)  
**Invariants:** Exactly the five seeded names for Part A demo (additional equipment not required).

---

### 3.2 `batch`

| Item | Detail |
|------|--------|
| **Purpose** | Manufacturing batch date window and label |
| **Primary key** | `id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| name | VARCHAR(128) | NO | |
| start_date | DATE | NO | Inclusive start of batch window |
| end_date | DATE | NO | Exclusive end (consistent with ops) |

**Constraints:** `end_date > start_date`  
**Indexes:** (`start_date`, `end_date`)  
**Invariants:** DR-001 — all child unit ops contained in `[start_date, end_date)`.

**Note:** Assignment does not state whether batch `end_date` is exclusive. **Design Decision / Implementation Choice:** treat batch bounds with the same exclusive-end convention as unit operations for consistent containment checks; document in README.

---

### 3.3 `unit_operation`

| Item | Detail |
|------|--------|
| **Purpose** | Scheduled unit operation block |
| **Primary key** | `id` |
| **FKs** | `batch_id` → `batch.id`; `equipment_id` → `equipment.id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| name | VARCHAR(128) | NO | |
| type | VARCHAR(32) | NO | CHECK IN (`Seed`,`Bioreactor`,`TFF`,`Spray`,`Sum`) |
| color | VARCHAR(32) | NO | UI color token/hex |
| status | VARCHAR(32) | NO | CHECK IN (`draft`,`confirmed`,`completed`) |
| start_date | DATE | NO | Inclusive |
| end_date | DATE | NO | Exclusive |
| batch_id | INTEGER | NO | FK |
| equipment_id | INTEGER | NO | FK |

**Constraints:** `end_date > start_date`  
**Indexes:** (`equipment_id`, `start_date`, `end_date`); (`batch_id`); (`status`)  
**Relationships:** N ops → 1 batch; N ops → 1 equipment  
**Invariants:** DR-001–DR-005 enforced in application layer (DB CHECKs cannot express pairwise overlap alone).

---

### 3.4 `unit_operation_dependency`

| Item | Detail |
|------|--------|
| **Purpose** | Explicit must-finish-before link |
| **Primary key** | `id` |
| **FKs** | `from_unitop_id`, `to_unitop_id` → `unit_operation.id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| from_unitop_id | INTEGER | NO | Source (must finish first) |
| to_unitop_id | INTEGER | NO | Target |

**Constraints:** `from_unitop_id <> to_unitop_id`; UNIQUE(`from_unitop_id`, `to_unitop_id`)  
**Indexes:** (`from_unitop_id`); (`to_unitop_id`)  
**ON DELETE:** RESTRICT when either op is referenced (chosen — audit clarity; see ADR-013).

---

### 3.5 `reading`

| Item | Detail |
|------|--------|
| **Purpose** | Time-series device readings (DO, pH, temp, feed_rate) |
| **Primary key** | `id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| time_h | FLOAT | NO | Process time hours from inoculation |
| signal_name | VARCHAR(32) | NO | `DO`, `pH`, `temp`, `feed_rate` |
| value | FLOAT | NO | |
| unit | VARCHAR(16) | NO | `%`, `-`, `degC`, `mL/h` |
| created_at | DATETIME/TIMESTAMPTZ | NO | Wall-clock ingest time (UTC) |

**Indexes:** (`signal_name`, `time_h`); (`time_h`)  
**Invariants:** Append-oriented; corrections via new rows only if ever needed (not required).  
**Optional:** UNIQUE(`signal_name`, `time_h`) — Design Decision / Implementation Choice (simulator may retry; prefer upsert or allow duplicates carefully).

---

### 3.6 `prediction`

| Item | Detail |
|------|--------|
| **Purpose** | Immutable forecast history for DO (and extensible signals) |
| **Primary key** | `id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| made_at_time_h | FLOAT | NO | Process time when forecast was produced |
| target_time_h | FLOAT | NO | Process time of predicted point |
| signal_name | VARCHAR(32) | NO | Typically `DO` |
| value | FLOAT | NO | Predicted value |
| unit | VARCHAR(16) | NO | `%` for DO |
| model_version | VARCHAR(64) | YES | Artifact/version id |
| created_at | DATETIME/TIMESTAMPTZ | NO | Wall-clock |

**Indexes:** (`made_at_time_h`); (`signal_name`, `made_at_time_h`); (`target_time_h`)  
**Invariants:** **Never UPDATE** prediction value rows to “correct” history; new forecast ⇒ new rows.  
**Shape:** One forecast event ⇒ typically 10 rows (`target_time_h` = made_at + 1/60 … + 10/60 hours).

---

### 3.7 `control_command`

| Item | Detail |
|------|--------|
| **Purpose** | Accepted and rejected feed setpoint commands |
| **Primary key** | `id` |

| Column | Type | Null | Notes |
|--------|------|------|-------|
| id | INTEGER | NO | PK |
| setpoint_name | VARCHAR(32) | NO | e.g. `feed_rate` |
| value | FLOAT | NO | Requested setpoint |
| unit | VARCHAR(16) | NO | `mL/h` |
| apply_at_time_h | FLOAT | NO | Process time to apply |
| status | VARCHAR(32) | NO | See §4 |
| reject_reason | TEXT | YES | Required when status=`rejected` |
| source | VARCHAR(32) | YES | `controller` \| `manual` \| other |
| created_at | DATETIME/TIMESTAMPTZ | NO | Wall-clock |

**Indexes:** (`setpoint_name`, `status`); (`apply_at_time_h`); (`created_at`)  
**Invariants:** Rejected rows retained for live page; pending uniqueness per setpoint enforced in application (command validation).

---

## 4. Command Status

| Status | Meaning |
|--------|---------|
| `accepted` | Passed validation (may still be waiting for apply time) |
| `pending` | Accepted and not yet applied / still blocking new same-setpoint commands — **Design Decision / Implementation Choice:** use `pending` vs fold into `accepted` with `applied_at` |
| `applied` | Simulator/device has taken the setpoint (optional tracking) |
| `rejected` | Failed validation; `reject_reason` set |

Assignment requires storing rejected commands with reason. Exact state machine beyond reject vs accept is Design Decision / Implementation Choice; must support “another command for the same setpoint is still pending.”

---

## 5. Timestamps and Time Axes

| Concept | Storage | Use |
|---------|---------|-----|
| Process time | `time_h`, `apply_at_time_h`, `made_at_time_h`, `target_time_h` | Control loop, charts, lag |
| Wall-clock | `created_at` | Audit, debugging, hosting ops |
| Calendar dates | `DATE` on schedule entities | Gantt / business rules |

Do not use wall-clock to decide actuator lag or forecast horizon.

---

## 6. Seed Data (scheduling)

- ≥3 batches across equipment.
- ≥2 deliberate violations (e.g., one DR-003 double-book and one DR-002 ordering violation) present after seed.
- Exact seed content: Design Decision / Implementation Choice; document locations in README.

---

## 7. Migrations

- Alembic for all schema changes.
- No silent schema drift; update this document when schema changes.

---

## 8. Out of Scope Tables (for now)

- Users/auth
- Multi-vessel registry (unless E4)
- Training run metadata store (filesystem model artifact is enough for PoC)

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial schema |
| 0.2 | 2026-09-29 | Confirmed ON DELETE RESTRICT (ADR-013); Phase 1 implemented |
