# Frontend Specification

**Document ID:** `07-FRONTEND_SPEC`  
**Scope:** Desktop-only Schedule page + Live Control page  
**Stack choice:** React + TypeScript (ADR-003)  

---

## 1. Relationship to Backend

- Frontend is a **presentation and interaction** layer.
- Scheduling validation (**DR-001–DR-005**) and command validation are **authoritative on the backend**.
- UI may disable obviously invalid inputs for UX (e.g., empty fields) but must not re-implement domain rules as truth.
- Always render violations/messages returned by the API.
- API client lives in a dedicated module (`src/api/…`); pages do not scatter raw `fetch` with duplicated URLs.

---

## 2. Application Pages

| Route (suggested) | Page |
|-------------------|------|
| `/` or `/schedule` | Schedule Gantt |
| `/control` | Live closed-loop control |

Routing library: Design Decision / Implementation Choice.

---

## 3. Schedule Page

### 3.1 Layout (desktop)

```text
+------------------------------------------------------------------+
|  Schedule                          [Start date] [End date] [Go]  |
+------------------------------------------------------------------+
| Equipment |  -------- date axis (scrollable) ----------------    |
| 1.5L      |  [==== Batch envelope =================]             |
|           |     [Seed][Bioreactor]                                |
| 15L       |           [==== Batch envelope ====]                 |
|           |              [TFF]                                    |
| ...       |                                                      |
+------------------------------------------------------------------+
| Violations list (optional panel)                                 |
+------------------------------------------------------------------+
```

### 3.2 Requirements checklist

| Requirement | Detail |
|-------------|--------|
| Equipment lanes | One horizontal lane per equipment (y-axis), seeded names |
| Date axis | x-axis calendar/day ticks |
| Scrollable range | Horizontal scroll within visible window; controls to set visible start/end dates |
| Operation blocks | Color-coded by `color` field; positioned by start/end on equipment lane |
| Batch grouping | Visual **batch envelope** grouping all ops of one batch (assignment Figure 1 style) |
| Edit UX | Click op → modal or drawer |
| Editable fields | start, end, equipment (from predefined list), status (`draft`/`confirmed`/`completed`) |
| Violation highlight | Ops in `violations[].operation_ids` get red border / alert symbol |
| Violation messages | Hover and/or list panel showing backend messages |
| Status editing | Via modal/drawer; completed immutability enforced by API errors |

### 3.3 Edit modal / drawer

- Load current op fields.
- On save → `POST` or `PUT` then refresh schedule or patch local state from response.
- Display returned violations inline.
- On delete → confirm; handle DR-005 error.

### 3.4 Loading / error

- Loading skeleton or spinner for schedule fetch.
- Toast or banner for API failures.
- Empty range message if no ops.

### 3.5 Non-requirements (base)

- Drag-and-drop (E3 optional).
- Mobile layout.
- AI assistant chat (E1 optional).

### 3.6 Wireframe — violation highlight

```text
  |  [Seed A]     [Seed B]   <- Seed B has red border + ⚠
  |               ________
  |              | conflict|
  |              | message |
```

---

## 4. Control Page

### 4.1 Layout (desktop)

```text
+------------------------------------------------------------------+
| Live Control     Process time: 12.40 h    Sim: running @ 60x     |
+------------------------------------------------------------------+
| DO (%DO) ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ forecast - - - -       |
|           ^ commands marked                                      |
+------------------------------------------------------------------+
| Feed (mL/h) ________________________________                     |
+------------------------------------------------------------------+
| Manual setpoint: [ 8.0 ] [Send]                                  |
| Rejected commands:                                               |
|  - 12.10 h value 35 rejected: outside bounds                     |
+------------------------------------------------------------------+
```

### 4.2 Requirements

| Element | Requirement |
|---------|-------------|
| DO chart | Time series vs process time |
| Feed rate chart | Time series vs process time |
| Latest forecast | Overlay on DO chart (10 points) |
| Command markers | Mark every command on time axis |
| Manual feed setpoint | Input + submit → `POST /command` |
| Rejected commands | List with reasons |
| Current process time | Displayed |
| Simulator state | Running/stopped/speed if exposed by API — Design Decision / Implementation Choice |
| Connection states | Loading, error, disconnected/retry |

### 4.3 Polling

Assignment: polling every few seconds is enough.  
**Design Decision / Implementation Choice:** e.g. 2–3 s poll of `/api/control/state` (implementation extension endpoint).

### 4.4 Charts library

Design Decision / Implementation Choice (e.g. lightweight chart lib). Prefer process-time x-axis labels in hours/minutes.

---

## 5. Shared UI Rules

- Desktop-focused breakpoints; no requirement for mobile nav.
- Accessibility where practical: labels on inputs, keyboard focus in modal, contrast for violation red.
- Do not block UI forever on forecast training — training is offline.

---

## 6. State Management

**Design Decision / Implementation Choice:** React Query / SWR for server state, or simple `useEffect` polling for PoC. Avoid duplicating schedule truth in a client-only store that can diverge from backend.

---

## 7. Out of Scope Visual Polish

Assignment: “How the page looks and feels beyond this is up to you.” Mature Figure 2 features are nice-to-have, not mandatory.

---

## Document control

| Version | Date | Notes |
|---------|------|-------|
| 0.1 | 2026-09-29 | Initial UI spec |
