# Product Backlog — User Stories

> \*\*Status note (July 2026).\*\* This backlog was written at project start. It has been
> updated to reflect what was actually delivered in the Capstone. Legend:
> \*\*✅ Delivered\*\* · \*\*🔄 Rescoped\*\* (delivered in a different form than originally
> planned — the story text below describes what was actually built) ·
> \*\*⏳ Future work\*\* (deliberately descoped from the Capstone; see final section).
>
> The biggest scope decision: the original plan covered four data areas
> (production counts, downtime, quality checks, material usage). During schema
> design against the real brewery workbook (A-04), scope was narrowed to do \*\*one
> area — downtime / loss events — end to end and well\*\*: validated entry, derived
> durations, supervisor review with anomaly detection, an approve/lock lifecycle,
> and a legacy-format Excel export. The other areas remain future work.

Trello board columns: **Backlog / To Do / Doing / In Review / Done**.
Format: `STORY-ID — As a <role>, I want <capability>, so that <benefit>.`

\---

## EPIC A — Foundation ✅

### A-01 — Repository and CI ✅

**As the developer, I want a GitHub repo with passing CI, so that quality is enforced from day one.**

* Repo created, shared with `quantic-grader`
* `.github/workflows/ci.yml` runs ruff (lint + format check) and pytest with coverage on Python 3.11 and 3.12
* Branch protection on `main`: pull requests only, CI must pass
* README documents local setup

### A-02 — Render demo deployment ✅

**As the developer, I want a deployed app on Render, so that the deployment pipeline exists from the start.**

* `render.yaml` in repo; push to `main` triggers Render build
* `/health` returns `OK` over the public URL: https://bottling-line-demo.onrender.com
* Known free-tier limitation (documented): SQLite storage is ephemeral; seed data
(users, lookups) is recreated on each deploy, entered shift data does not persist
across redeploys. Production target is the brewery intranet with persistent storage.

### A-03 — Trello board set up ✅

**As the Product Owner, I want a Trello board so that all stories are tracked.**

* Board created with all stories as cards
* Link in README

### A-04 — Schema derived from real Excel ✅ 🔄

**As the developer, I want the database schema mapped from the real bottling line Excel, so that the system fits actual operator workflow.**

* Real brewery workbook reviewed; schema deliberately narrowed to the downtime log
* Tables actually implemented (7): `user`, `shift`, `loss\_event`, and four lookup
tables — `sku`, `machine`, `bcs\_category` (locked 5-category standard),
`loss\_type` (with `suggested\_bcs\_code` for guided entry)
* Core design decision: `loss\_event` stores **only typed values** (date, start,
stop, dropdown selections, two free-text failure descriptions). All durations
and calendar fields are **derived**, never stored — eliminating the
inconsistent-duplicate-columns problem of the legacy sheet
* Originally planned `production`, `quality\_checks`, `material\_usage`, and
`audit\_log` tables were descoped with the functional areas they served
(audit needs are covered by lifecycle fields on `shift`: operator\_id,
supervisor\_id, opened/closed/approved timestamps)

\---

## EPIC B — Authentication \& Admin

### B-01 — User login ✅

**As any user, I want to log in with username and password, so that my actions are tracked.**

* `POST /login` accepts credentials, bcrypt-verified against `user` table
* Successful login stores user id in a signed session cookie
* Failed login shows one generic error for unknown-user and wrong-password
(no username enumeration)
* Open-redirect-safe `?next=` returns the user to their original destination
* Tested in `tests/integration/test\_auth.py` and `tests/unit/test\_auth\_service.py`

### B-02 — User logout ✅

**As any user, I want to log out, so that my session is secure.**

* `POST /logout` clears the session (POST, not GET, so a stray prefetch can't log
a user out) and redirects to the login screen
* Delivered together with B-01

### B-03 — Session expiry ✅ 🔄

**As an admin, I want sessions to expire after a configurable period, so that abandoned terminals don't stay logged in.**

* Implemented via signed-cookie `max\_age` from `settings.session\_lifetime\_minutes`
(default 480 = 8 hours); an expired cookie is invalid and the user is redirected
to login by the auth dependency
* Rescope note: enforced by cookie expiry rather than server-side session storage;
no dedicated automated test for the expiry itself

### B-04 — Role-based route protection ✅ 🔄

**As an admin, I want role separation enforced on routes, so that users only reach screens appropriate to their role.**

* `require\_role(...)` dependency; operator hitting `/supervisor/...` gets 403 (tested)
* Deliberate business decision during Sprint 1: **supervisors may also use the
operator entry screens** (they can key events as well as review them), so
operator routes allow operator, supervisor, and admin
* Tested for each role in `tests/integration/test\_auth.py` and `test\_supervisor.py`

### B-05 — Admin user management ⏳

Moved to Future Work (see below).

### B-06 — Lookup table CRUD ⏳

Moved to Future Work. Lookup vocabularies are currently maintained via the seed
script (`scripts/seed.py`, idempotent).

\---

## EPIC C — Operator Data Entry

### C-01 — Start a shift ✅

**As an operator, I want to start a new shift, so that my entries are grouped together.**

* `/operator/shift/new` form: date (default today), shift (A/B/C), line (optional)
* Opening a shift that already exists for that operator/date/name **resumes** it
instead of creating a duplicate
* Tested in `tests/integration/test\_start\_shift.py`

### C-02 — Log downtime / loss events ✅ 🔄

**As an operator, I want to record downtime events with times, machine, product, and reason, so that losses are tracked at the source.**
*(Originally "Log production counts"; rescoped when the project narrowed to the
downtime log. Original C-03 "Log downtime event" was merged into this story.)*

* Form: event date, start time, stop time, SKU (dropdown), machine (dropdown),
Type of Loss (dropdown), BCS category, two free-text failure descriptions
* **Guided entry with override**: choosing a Type of Loss auto-suggests the
standard BCS category via HTMX; the operator can override it
* Duration is calculated server-side from start/stop — operators never type it
* Validation: stop after start; events only on OPEN shifts
* Tested in `tests/integration/test\_operator\_form.py` and unit tests for
derivation and classification

### C-03 — Log downtime event 🔄

Merged into C-02 (the app has a single entry type: the loss event).

### C-04 — Log quality check ⏳ / C-05 — Log material usage ⏳

Moved to Future Work with the scope decision recorded in A-04.

### C-06 — Close shift ✅

**As an operator, I want to close my shift, so that the supervisor can review it.**

* "Close shift for review" button with confirmation
* Shift status `OPEN` → `PENDING\_REVIEW`; the entry form becomes read-only
* Only the owning operator (or an admin) can close a shift
* Enforced in the service layer, not just the UI; tested in `test\_supervisor.py`

### C-07 — Validation feedback ✅

**As an operator, I want clear validation errors at entry, so that I cannot save bad data.**

* Server-side validation (Pydantic schemas) is the source of truth
* Errors re-render the form with a visible message; invalid transitions and
timings surface as error banners rather than crashes

\---

## EPIC D — Supervisor Review ✅

### D-01 — Supervisor dashboard ✅

**As a supervisor, I want a list of shifts pending review, so that I know what needs attention.**

* `/supervisor` groups shifts by status: Pending review / Approved / Locked
* Each row: date, shift, line, operator, event count, total downtime (derived),
and an **anomaly count** badge
* Role-gated to supervisor/admin; tested in `tests/integration/test\_supervisor.py`

### D-02 — Review a shift ✅ 🔄

**As a supervisor, I want to drill into a shift's data, so that I can verify accuracy.**

* Single review page (not tabs — one data area) showing every loss event with
derived durations, plus shift metadata and total downtime
* Anomalies listed prominently above the events with severity badges
* Rescope note: original story assumed four tabs (production/downtime/quality/
materials); the delivered system has one data area

### D-03 — Edit an entry with reason ⏳

Moved to Future Work. In the delivered lifecycle, pre-review corrections are made
by the operator while the shift is OPEN; after submission the record is
read-only, and LOCKED shifts would require an admin override (not yet built).

### D-04 — Anomaly detection ✅

**As a supervisor, I want anomalies flagged automatically, so that I focus review on real issues.**

* Strategy pattern: each rule is an independent class in a registry; adding a
rule never touches existing rules (Open/Closed)
* **Three rules delivered** (target was "at least 2"):

  1. Long breakdown — single event > 30 min (warning), > 60 min (critical)
  2. High total downtime — shift total > 120 min (warning), > 240 min (critical)
  3. Repeated machine failure — same machine ≥ 3 events in a shift
* Anomalies are computed at review time, never stored, so rule changes need no
migration; unit-tested per rule and shown live on dashboard + review page

### D-05 — Approve and lock shift ✅ 🔄

**As a supervisor, I want to approve and then lock a shift, so that the data becomes the official, immutable record.**

* Delivered as an explicit **two-step** lifecycle (original story combined them):
`PENDING\_REVIEW` → **Approve** → `APPROVED` → **Lock** → `LOCKED`
* Every transition guarded in the service layer; illegal transitions (approving
an open shift, locking before approval) surface as error banners, not 500s
* Approval records `supervisor\_id` and `approved\_at` (audit fields)
* Tested: transition unit tests + full approve-then-lock integration flow

\---

## EPIC E — Analytics \& Export

### E-01 — KPI dashboard ⏳

Moved to Future Work.

### E-02 — Excel export, legacy format ✅ 🔄

**As a supervisor, I want to export a shift in the legacy Excel format, so that downstream consumers aren't disrupted.**

* `GET /supervisor/shift/{id}/export.xlsx`, role-gated, streamed as a download
* Output matches the real brewery workbook's **18-column layout exactly**
(verified against the actual legacy sheet, including header wording and order:
S/N., Date, Event Start, Event Stop, SKU, BCS Losses, Type of Loss, Machine,
the two failure descriptions, three duration forms, and five calendar fields)
* All derived columns are computed from stored values; derivation is unit-tested
against real April-2020 workbook data
* Rescope note: single sheet (one data area), not the originally planned four
sub-area sheets

### E-03 — Bulk export ⏳ / E-04 — Audit trail viewer ⏳

Moved to Future Work (lifecycle audit fields exist on `shift`; a viewer does not).

\---

## EPIC F — Deployment \& Documentation

### F-01 — Render demo with seed data ✅ 🔄

**As a grader, I want the Render demo usable without setup, so that I can evaluate immediately.**

* Render build seeds users and full lookup vocabularies (idempotent seed script)
* Demo accounts documented in README (`operator1` / `super1` / `admin`,
password = username; demo-only credentials, bcrypt-hashed at rest)
* Rescope note: no synthetic 30-day dataset — the demo flow is to create a shift
live, which the recorded demonstration walks through end to end

### F-02 — Docker image ✅

**As a brewery IT admin, I want a Docker image I can run on-premises, so that no manual install is needed.**

* `Dockerfile` at repo root produces a single image; `/health` endpoint for checks

### F-03 — Design and testing document ✅

**As a grader, I want a complete design and testing document, so that I can evaluate the engineering choices.**

* Delivered as `docs/Design\_and\_Testing\_Document\_FINAL.pdf`: problem, requirements
(FR-1–FR-9), architecture with diagram, design decisions and patterns, data
model, security, testing strategy with per-module breakdown (95 automated
tests), a requirements-to-tests traceability matrix, results, deployment,
limitations
* `docs/DESIGN.md` retains the working design notes

### F-04 — Demo recording ✅

**As a grader, I want a 15–20 min screen recording with voice-over, so that I can see the system in action.**

* Recorded with Zoom; government-issued ID shown on camera at the start;
presenter visible on webcam throughout
* Walks the full lifecycle: operator login → open shift → enter events (guided
BCS entry, derived durations) → close for review → supervisor dashboard →
anomaly review → approve → lock → legacy Excel export → repo, tests, and CI
* Final length 19:34; link submitted via the Quantic dashboard (Google Drive,
link-sharing enabled)

### F-05 — Final submission ✅

**As the student, I want all Capstone artifacts submitted, so that I receive credit.**

* GitHub repo (shared with `quantic-grader`) containing the code, the design and
testing document, and links to the deployed app and Trello board
* Presentation link submitted via the Quantic dashboard

\---

## Future work (deliberately outside Capstone scope)

Recorded as scope decisions, not omissions — the Capstone delivered one data
area end to end rather than four areas thinly:

* **B-05 Admin user management** — create/deactivate accounts, reset passwords via UI
* **B-06 Lookup table CRUD** — manage SKUs, machines, loss types, BCS in-app
(currently via idempotent seed script)
* **C-04 Quality checks / C-05 Material usage** — additional data areas from the
original workbook
* **D-03 Supervisor edit-with-reason** — auditable corrections post-submission,
with an admin override path for LOCKED shifts
* **E-01 KPI dashboard** — downtime trends, Pareto by reason, toward OEE reporting
* **E-03 Bulk export** — date-range, multi-shift legacy workbook in one click
* **E-04 Audit trail viewer** — UI over the lifecycle audit fields
* **Persistence on the demo deployment** — PostgreSQL (the repository pattern
makes this a configuration change)
* Stretch items from the original backlog (Playwright E2E, BI integration,
email digests, mobile-responsive screens) remain unstarted

