# BBP Bioprocessor — User Manual

**Open the app here:** https://bioprocessor.onrender.com  

This guide explains how to use the software. You do **not** need to install anything.  
Just open the link in a web browser (Chrome, Edge, or Firefox work well). Prefer a **desktop** or laptop screen — the app is designed for desktop use.

> **Note:** The free hosted version may take **30–60 seconds** to wake up the first time you open it after a break. Wait until the page loads; then it should feel normal.

---

## What this software does

BBP Bioprocessor helps with two jobs:

1. **Schedule** — Plan batches and unit operations on shared equipment, and see when the plan breaks scheduling rules.
2. **Live Control** — Watch dissolved oxygen (DO) and feed rate for a bioreactor demo, see a short forecast, and send feed commands.

Use the top navigation:

| Link | Opens |
|------|--------|
| **Schedule** | Planning board (Gantt chart) |
| **Control** | Live bioreactor control page |

---

## Part 1 — Schedule page

**Open:** https://bioprocessor.onrender.com/  
(or click **Schedule** in the top bar)

### What you see

- **Equipment lanes** down the left (e.g. 1.5L, 15L, 75L, 1500L).
- A **timeline** of dates across the top.
- Colored **blocks** = unit operations (Seed, Bioreactor, TFF, etc.).
- Blocks belonging to the same **batch** are grouped visually.
- A **violations** list (rule problems) appears when something is wrong with the schedule.

### Choose the date range

At the top you can set **start** and **end** dates for the visible window, then apply them.

- Use a range that covers your plan (the demo seed data is roughly **Oct–Nov 2025**).
- If you see an empty board, widen the date range.

### Read a unit operation

Each colored block shows work on one piece of equipment for one batch.

- **Name** — e.g. “Charlie Bioreactor 1500L”
- **Type** — Seed, Bioreactor, TFF, Spray, or Sum
- **Status** — draft, confirmed, or completed

### Edit an operation

1. **Click** a colored block.
2. A side panel (drawer) opens.
3. You can change:
   - Start date  
   - End date  
   - Equipment  
   - Status  
4. Click **Save**.

The system checks the whole schedule against the business rules and updates the violations list.

### Important: how dates work

An operation’s **end date is exclusive**.  
Example: if something ends on **Oct 24**, it is **finished before** Oct 24 starts — so another job may begin on Oct 24 without overlapping that day.

### Scheduling rules (plain language)

The software enforces these rules:

| Rule | Meaning |
|------|---------|
| **Batch containment** | An operation must stay inside its batch’s start/end window. |
| **Process ordering** | Later process types (e.g. Bioreactor) must not start before every earlier type (e.g. Seed) in the same batch has finished. |
| **No double-booking** | Two operations cannot use the **same equipment** at the same time. |
| **Dependencies** | If A must finish before B, B cannot start before A ends. |
| **Completed is locked** | Once status is **completed**, you cannot move or delete that operation. |

### Violations

If a rule is broken:

- The board **highlights** involved operations.
- The **violations** panel shows a clear message naming the operations.

**What happens when you save with a problem?**  
The change is still saved, and the system shows the violations so you can fix them (except for **completed** operations — those edits are blocked).

### Demo violations already in the data

The sample schedule includes deliberate problems so you can practice:

1. **Equipment conflict** — Bravo Bioreactor and Charlie Seed both on **1.5L** at overlapping times.  
2. **Ordering problem** — Charlie Bioreactor starts before Charlie Seed on **75L** has finished.

**Try this:** open **Charlie Bioreactor 1500L**, move its start date to **2025-10-24** (or later), save — the ordering violation with Seed 75L should clear.

### Delete an operation

Open the operation drawer and use **Delete** if available.  
You cannot delete a **completed** operation.

---

## Part 2 — Live Control page

**Open:** https://bioprocessor.onrender.com/control  
(or click **Control** in the top bar)

### What this page is for

It shows a **demo** of closed-loop bioreactor monitoring:

- Recent **dissolved oxygen (DO)** and **feed rate**
- A short **forecast** of DO for the next 10 minutes
- **Commands** that change feed rate
- A list of **rejected** commands (with reasons)

The page **refreshes automatically** every few seconds.

### Status strip (top)

| Label | Meaning |
|-------|---------|
| **Process time** | Simulated time inside the fermentation (in hours), not your wall-clock time. |
| **Readings** | How many sensor samples are stored. |
| **Forecast** | Model name and when the forecast was made — or “unavailable” if there is not enough history yet. |
| **Link** | **live** = connected to the server; **error** = connection problem (try refresh; wait if the host is waking up). |

### Charts

1. **Dissolved oxygen (% DO)**  
   - Solid line = measured DO  
   - Dashed line = **forecast** (next ~10 process-minutes)  
   - Vertical markers = feed **commands** (blue/ok vs red/rejected)

2. **Feed rate (mL/h)**  
   - Solid line = measured / applied feed  
   - Same command markers on the time axis  

### Play a fermentation run

Charts only move when new process minutes are ingested. On the hosted demo, use the **Play A / Play B / Play C** buttons:

1. Click **Play A** (or B / C) — process time advances about **one minute per wall-clock second**.  
2. Watch DO and feed traces extend; forecast refreshes as history grows.  
3. Click **Stop** when you want to pause.  
4. If Send is blocked because a command is still pending, click **Cancel pending**.

While a run is playing, accepted feed commands apply automatically when process time reaches their apply time (no separate simulator needed).

### Manual feed setpoint

1. Enter a number between **0** and **30** (units: **mL/h**).  
2. Click **Send**.

**Examples:**

| Value | What happens |
|-------|----------------|
| `8` | Accepted (if no other command is waiting) |
| `15` | Accepted (stronger feed) |
| `35` | **Rejected** — outside allowed range |

Accepted commands apply at **current process time + 5 minutes** (actuator lag).  
With **Play** running, you will see feed respond once process time reaches that apply time.

### Run controller step

Click **Run controller step** to let the **automatic rule-based controller** decide a feed change from the latest DO and feed.

- If it acts, a new pending command appears (same validation rules as manual).  
- If it holds, you will see a short reason (e.g. already waiting, or “dwell” time between commands).

### Rejected commands

The right-hand list shows every failed command and **why**, for example:

- Value outside 0–30 mL/h  
- Apply time earlier than current process time  
- Wrong unit  
- Another feed command is still **pending**

**Tip:** Only **one** pending feed command is allowed at a time. Use **Cancel pending** to clear a stuck wait, or keep **Play** running until the apply time is reached.

---

## Quick tour (about 3 minutes)

1. Open https://bioprocessor.onrender.com/ — wait if it is waking up.  
2. On **Schedule**, find the highlighted violations.  
3. Click **Charlie Bioreactor 1500L**, set start to **2025-10-24**, save — watch a violation clear.  
4. Open **Control**.  
5. Click **Play A** and watch the DO/feed charts move.  
6. Send feed **`8`**, then try **`35`** to see a rejection.  
7. Optionally click **Run controller step**. Use **Cancel pending** if Send is blocked.

---

## Troubleshooting (no technical setup)

| Problem | What to try |
|---------|-------------|
| Page is blank / slow | Wait up to a minute; free hosting sleeps when idle. Refresh. |
| Schedule looks empty | Expand the date range to include **Oct–Nov 2025**. |
| Cannot edit an operation | It may be **completed** (locked). |
| Charts not moving | Click **Play A** (or B / C). Stop first if another run is already playing. |
| Forecast unavailable | Needs enough recent DO + feed history; play a run for a minute, then refresh. |
| Send rejected “still pending” | Click **Cancel pending**, or keep Play running until the previous command applies. |
| Link shows error | Refresh the page; if the host just woke up, wait and refresh again. |

---

## Glossary

| Term | Plain meaning |
|------|----------------|
| **Batch** | A production campaign that groups several unit operations. |
| **Unit operation** | One step of work (e.g. Seed, Bioreactor) on one equipment item. |
| **Equipment** | A vessel or resource lane (e.g. 1.5L, 1500L). |
| **Violation** | A scheduling rule that is currently broken. |
| **Process time** | Simulated time inside the fermentation run (hours from start). |
| **DO** | Dissolved oxygen (%). |
| **Feed rate** | How fast feed is pumped (mL/h). Allowed range **0–30**. |
| **Forecast** | Predicted DO for the next 10 process-minutes. |
| **Pending command** | A feed change that is accepted but not yet applied. |

---

## Support contact (optional)

If something looks wrong with the hosted demo, contact the person who shared this link and include:

- Which page (Schedule or Control)  
- What you clicked  
- A short description or screenshot  

---

*BBP Bioprocessor — user-facing guide. For technical setup and development, see the project README (not required for normal use).*
