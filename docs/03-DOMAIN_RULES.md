# Domain Rules — Scheduling

**Document ID:** `03-DOMAIN_RULES`  
**Source:** Assignment Part A business rules  
**Authority:** Backend only  

---

## 1. Shared Definitions

### 1.1 Date intervals

- Unit operations and batches have `start_date` and `end_date`.
- **End dates are exclusive** (half-open interval `[start, end)`).
- An operation ending on date `D` frees equipment on `D`; another operation may start on `D` without overlap.

**Non-overlap example:**

| Op | Interval |
|----|----------|
| A | Oct 1 → Oct 4 |
| B | Oct 4 → Oct 6 |

A and B do **not** overlap.

**Overlap example:**

| Op | Interval |
|----|----------|
| A | Oct 24 → Oct 31 |
| B | Oct 29 → Nov 4 |

Overlap on Oct 29–Oct 30 (inclusive calendar days that fall in both half-open ranges).

### 1.2 Overlap predicate

Two half-open intervals `[s1, e1)` and `[s2, e2)` overlap iff:

```text
s1 < e2 AND s2 < e1
```

### 1.3 Process type order

```text
Seed < Bioreactor < TFF < Spray < Sum
```

A batch need not include every type. Ordering applies among types that are present.

### 1.4 Violation reporting

- Readable message naming the operations involved.
- **Report each violating pair once per rule** (no duplicate messages for the same pair under the same rule).
- Completing ops may participate in pairwise checks except where rule preconditions exclude them (see each rule).

### 1.5 Pair identity

For pairwise rules, treat unordered pair `{op_a, op_b}` as one pair unless the rule is directed (dependency / process ordering may be directed — see each rule).

---

## 2. Rule Catalog

### DR-001 — Batch Containment

| Field | Content |
|-------|---------|
| **Rule ID** | DR-001 |
| **Name** | Batch containment |
| **Description** | Every unit operation of a batch must lie within the batch’s start and end dates. |
| **Preconditions** | Unit operation has a `batch_id`; batch has `start_date`, `end_date`. |
| **Validation logic** | Let batch interval be `[B.start, B.end)` and op `[O.start, O.end)`. Valid iff `O.start >= B.start` AND `O.end <= B.end`. (Op must be fully contained; end exclusive semantics apply consistently to both.) |
| **Example valid** | Batch Oct 1 → Nov 1; Seed Oct 5 → Oct 10. |
| **Example invalid** | Batch Oct 1 → Oct 20; Bioreactor Oct 15 → Oct 25 (op end past batch end). |
| **Expected violation message** | Pattern: `Unit operation "{op}" is outside batch "{batch}" date range [{batch_start}, {batch_end}).` (exact wording Design Decision / Implementation Choice; must name ops/batch.) |
| **Operations involved** | The violating unit operation and its batch (identify batch by name/id in message). |

---

### DR-002 — Process Ordering

| Field | Content |
|-------|---------|
| **Rule ID** | DR-002 |
| **Name** | Process type ordering |
| **Description** | Unit operations follow Seed → Bioreactor → TFF → Spray → Sum. A later type may not start before every earlier type in the **same batch** has ended. |
| **Preconditions** | Compare unit operations in the same `batch_id` with different types in the ordered sequence. |
| **Validation logic** | For each op `L` of later type and each op `E` of earlier type in the same batch: require `L.start_date >= E.end_date`. If any earlier-type op has not ended before `L` starts, violation for that directed pair `(E, L)`. |
| **Example valid** | Seed on 1.5L Oct 21 → Oct 24; Bioreactor on 15L starts Oct 24. |
| **Example invalid** | Same Seed; Bioreactor starts Oct 23. |
| **Expected violation message** | Pattern: `"{later}" ({later_type}) starts before "{earlier}" ({earlier_type}) ends in batch "{batch}".` |
| **Operations involved** | The earlier-type op and the later-type op (one message per such violating pair). |

**Design Decision / Implementation Choice:** If multiple ops share a type, still require every earlier-type instance to have ended before a later-type starts (strict reading of “every earlier type”). **Chosen and implemented** in `scheduling_rules.py`.

---

### DR-003 — Equipment Double-Booking

| Field | Content |
|-------|---------|
| **Rule ID** | DR-003 |
| **Name** | Equipment exclusivity |
| **Description** | The same equipment cannot be used by two unit operations at the same time, regardless of batch. |
| **Preconditions** | Two distinct unit operations with the same `equipment_id`. |
| **Validation logic** | If intervals overlap under §1.2, violation. |
| **Example valid** | Op A on 1.5L Oct 1 → Oct 4; Op B on 1.5L Oct 4 → Oct 6. |
| **Example invalid** | Bioreactor on 1.5L Oct 24 → Oct 31 and Seed on 1.5L Oct 29 → Nov 4. |
| **Expected violation message** | Pattern: `Equipment "{equipment}" double-booked by "{op1}" and "{op2}".` |
| **Operations involved** | The two overlapping unit operations (unordered pair; report once). |

---

### DR-004 — Explicit Dependency

| Field | Content |
|-------|---------|
| **Rule ID** | DR-004 |
| **Name** | Explicit must-finish-before dependency |
| **Description** | An explicit dependency’s target may not start before its source has ended. |
| **Preconditions** | A `UnitOperationDependency` from `from_unitop_id` (source) to `to_unitop_id` (target). |
| **Validation logic** | Require `target.start_date >= source.end_date`. |
| **Example valid** | Source ends Oct 10; target starts Oct 10. |
| **Example invalid** | Source ends Oct 10; target starts Oct 9. |
| **Expected violation message** | Pattern: `Dependency violated: "{target}" starts before "{source}" ends.` |
| **Operations involved** | Source and target unit operations (directed pair; once per dependency/rule). |

---

### DR-005 — Completed Operation Immutability

| Field | Content |
|-------|---------|
| **Rule ID** | DR-005 |
| **Name** | Completed operation immutability |
| **Description** | A completed unit operation cannot be moved or deleted. |
| **Preconditions** | Existing unit operation with `status = completed`. |
| **Validation logic** | **DELETE:** always reject. **UPDATE / “move”:** reject if any of `start_date`, `end_date`, `equipment_id` change. **Chosen:** also disallow changing status away from `completed`; allow no-op updates that change nothing material (ADR-014). |
| **Example valid** | Update a `draft` op’s dates; delete a `confirmed` op. |
| **Example invalid** | Change `start_date` of a `completed` op; DELETE a `completed` op. |
| **Expected violation message** | Pattern: `Completed unit operation "{op}" cannot be moved or deleted.` |
| **Operations involved** | The completed unit operation. |

---

## 3. Evaluation Order (recommended)

Design Decision / Implementation Choice — suggested order for clarity:

1. DR-005 (immutability / delete guard) before mutating.
2. DR-001 (containment).
3. DR-002 (process ordering).
4. DR-003 (equipment).
5. DR-004 (explicit dependencies).

All applicable violations for a save should be collected and returned together when using save-and-return or reject-with-list policies (ADR-005), rather than failing only on the first — **Design Decision / Implementation Choice** if fail-fast preferred; prefer collect-all for better UX.

---

## 4. Schedule-Wide vs Mutation-Scoped Checks

| Context | Behavior |
|---------|----------|
| `GET /api/schedule` | Evaluate current persisted schedule; return all current violations in range (ops involved intersecting the requested window — Design Decision / Implementation Choice if a violation’s pair has one op outside range: still include if either op intersects). |
| POST/PUT/DELETE | Evaluate rules affected by the mutation; apply ADR-005 save policy. |

---

## 5. Non-Scheduling Domain (pointer)

Command validation rules for Part C are specified in `06-ML_CONTROL_SPEC.md` (not DR-00x). Do not mix scheduling DR IDs with command validation.

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial rule IDs DR-001–DR-005 |
| 0.2 | 2026-09-29 | Phase 3 implemented; DR-005 + multi-type-instance choices locked |
