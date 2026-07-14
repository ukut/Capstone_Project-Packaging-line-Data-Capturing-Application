Product Backlog — User Stories
Copy each story below into a Trello card. Suggested Trello columns:
Backlog — everything starts here
Sprint 1 / Sprint 2 / Sprint 3 — move into the right sprint at planning
In Progress
In Review (self-review for solo project — write a brief commit comment summarizing what was checked)
Done
Format used: `[Sprint] STORY-ID — As a <role>, I want <capability>, so that <benefit>.` Acceptance criteria listed underneath.
---
EPIC A — Foundation (Sprint 0 / Foundation Week, May 26 – May 31)
> Not user-facing, but every Capstone deliverable depends on this being right.
A-01 — Repository and CI
As the developer, I want a GitHub repo with passing CI, so that quality is enforced from day one.
Repo created, shared with `quantic-grader`
`.github/workflows/ci.yml` runs ruff + pytest on every push
Branch protection on `main` (CI must pass)
README documents local setup
✅ This is already done in the scaffold
A-02 — Render demo deployment skeleton
As the developer, I want a deployed hello-world on Render, so that the deployment pipeline exists before there is anything important to deploy.
`render.yaml` in repo
Push to `main` triggers Render build
`/health` returns `OK` over the public URL
URL added to README
A-03 — Trello board set up
As the Product Owner, I want a Trello board so that all stories are tracked.
Board created
All stories from this file added as cards
Columns: Backlog / Sprint 1 / Sprint 2 / Sprint 3 / In Progress / In Review / Done
Link added to README
A-04 — Schema derived from real Excel
As the developer, I want the database schema mapped from the real bottling line Excel, so that the system fits actual operator workflow.
Excel workbook reviewed
Tables defined: users, shifts, production, downtime, quality_checks, material_usage, lookups (SKUs, machines, downtime_reasons, reject_categories), audit_log
SQLAlchemy models written in `app/models/`
ER diagram added to `docs/DESIGN.md` §4
---
EPIC B — Authentication & Admin (Sprint 1, June 1 – June 14)
B-01 — User login
As any user, I want to log in with username and password, so that my actions are tracked.
`POST /login` accepts credentials
bcrypt-verified against `users` table
Successful login creates session cookie
Failed login shows error, no information leakage
Tested in `tests/integration/test_auth.py`
B-02 — User logout
As any user, I want to log out, so that my session is secure.
`POST /logout` clears session
Redirects to login screen
B-03 — Session expiry
As an admin, I want sessions to expire after a configurable period, so that abandoned terminals don't stay logged in.
`SESSION_LIFETIME_MINUTES` enforced (default 480 = 8 hours)
Expired session redirects to login
Tested
B-04 — Role-based route protection
As an admin, I want operators blocked from supervisor screens and vice versa, so that role separation is enforced.
`require_role(Role.SUPERVISOR)` dependency
Operator hitting `/supervisor/...` gets 403
Tested for each role
B-05 — Admin user management
As an admin, I want to create, edit, deactivate user accounts, so that I control who can access the system.
`/admin/users` lists all users
Create new user (username, password, role)
Edit role / deactivate
Audit log entry on every change
B-06 — Lookup table CRUD
As an admin, I want to manage SKUs, machines, downtime reasons, and reject categories, so that operators have current dropdown options.
`/admin/lookups/skus`, `/admin/lookups/machines`, etc.
Create / edit / soft-delete (deactivate, not hard delete — preserves historical references)
Audit log entry on every change
---
EPIC C — Operator Data Entry (Sprint 2, June 15 – June 28)
C-01 — Start a shift
As an operator, I want to start a new shift, so that my entries are grouped together.
`/operator/shift/new` form: date (default today), shift (A/B/C), line, supervisor on duty
One open shift per user max
Reopening today's shift if already started
C-02 — Log production counts
As an operator, I want to record production counts per SKU, so that output is captured by hour or by batch.
Form: SKU dropdown, good_count, reject_count, reject_category (optional)
Validation: counts ≥ 0; reject_category required if reject_count > 0
Server-side validation mirrored client-side via HTMX
C-03 — Log downtime event
As an operator, I want to record downtime with start time, end time, machine, and reason, so that losses are tracked.
Form: start_time, end_time, machine (dropdown), reason (dropdown), comments (free-text, optional)
Duration calculated server-side from start/end
Validation: end > start; both within shift window
C-04 — Log quality check
As an operator, I want to record quality checks with measured values, so that QC is documented at the source.
Fields: timestamp, SKU, fill_volume, brix, CO2, cap_torque, label_position, pass/fail (auto from spec ranges)
Each field validated against the SKU's spec range
C-05 — Log material usage
As an operator, I want to record opening / received / closing for materials, so that consumption is captured.
Fields per material: opening, received, closing, calculated_used
Materials list comes from lookup table
C-06 — Close shift
As an operator, I want to close my shift, so that the supervisor can review it.
"Close shift" button on shift dashboard
Confirmation modal: "this submits all entries for supervisor review"
Shift status changes from `OPEN` to `PENDING_REVIEW`
Operator can no longer edit (only supervisor can after this point)
C-07 — Validation feedback
As an operator, I want clear validation errors at entry, so that I cannot save bad data.
Out-of-range numeric fields highlighted red with the valid range shown
Required fields cannot be skipped
Server-side validation is the source of truth (client validation is for UX only)
---
EPIC D — Supervisor Review (Sprint 2 ends / Sprint 3 starts)
D-01 — Supervisor dashboard
As a supervisor, I want a list of shifts pending review, so that I know what needs attention.
`/supervisor` lists shifts by status (Pending / Approved / Locked)
Shifts with anomalies flagged at the top
Each row shows date, line, operator, total production, anomaly count
D-02 — Review a shift
As a supervisor, I want to drill into a shift's data, so that I can verify accuracy.
Tabs for Production / Downtime / Quality / Materials
Each entry shows timestamp and entering operator
Anomalies highlighted inline
D-03 — Edit an entry with reason
As a supervisor, I want to correct an entry with a documented reason, so that corrections are auditable.
Edit button on any entry pre-shift-lock
Required reason field for every edit
Original value preserved in audit log
"Edited" badge shown next to the entry
D-04 — Anomaly detection
As a supervisor, I want anomalies flagged automatically, so that I focus review on real issues.
All registered `AnomalyRule` strategies evaluated on shift open for review
Anomalies shown inline (production tab shows reject-rate anomaly; downtime tab shows long-downtime anomaly)
At least 2 rules implemented and tested
D-05 — Approve and lock shift
As a supervisor, I want to approve a shift, so that the data becomes the official record.
"Approve" button on supervisor review screen
Confirmation: "this locks the shift; further edits require admin override"
Shift status: `PENDING_REVIEW` → `APPROVED` (read-only)
Audit log entry
---
EPIC E — Analytics & Export (Sprint 3, June 29 – July 8)
E-01 — KPI dashboard
As a supervisor, I want a dashboard of OEE and reject trends, so that I can spot patterns across shifts.
`/supervisor/dashboard` shows last 30 days
Charts: production by day, reject rate trend, downtime by reason (Pareto)
Filter by SKU, line, date range
E-02 — Excel export — legacy format
As a supervisor, I want to export a shift in the legacy Excel format, so that downstream consumers aren't disrupted.
`GET /supervisor/shift/{id}/export.xlsx`
Output matches the existing brewery workbook's column layout exactly
Includes all four sub-areas (production, downtime, quality, materials) as separate sheets
E-03 — Bulk export
As a supervisor, I want to export a date range to one workbook, so that monthly reports are one click.
Date range picker
Multi-shift workbook with one tab per shift
E-04 — Audit trail viewer
As an admin, I want to see all changes to a shift, so that accountability is maintained.
`/admin/audit?shift_id=...` shows append-only log
Each entry: timestamp, user, action, before/after values
---
EPIC F — Deployment & Documentation (Sprint 3 + Submission Week)
F-01 — Render demo with seed data
As a grader, I want the Render demo to show the full system with realistic data, so that I can evaluate without setup.
Render build runs `init_db` and `seed_synthetic`
30 days of synthetic shifts, varied SKUs, with a few engineered anomalies for the demo
Demo credentials documented in README
F-02 — Docker image for brewery
As a brewery IT admin, I want a Docker image I can run on-premises, so that no manual install is needed.
`Dockerfile` produces a single image
Documented `docker run` command
Health check passes
F-03 — Design and testing document finalized
As a grader, I want a complete design and testing document, so that I can evaluate the engineering choices.
`docs/DESIGN.md` filled in (all sections)
ER diagram included
Test pyramid described with actual coverage numbers
F-04 — Demo recording
As a grader, I want a 15–20 min screen recording with voice-over, so that I can see the system in action.
Recorded with Zoom (or similar)
Government-issued ID shown on camera
Walks through: operator login → enter shift → close → supervisor review → anomaly review → approve → Excel export → dashboard
Uploaded as unlisted YouTube video; link in README
F-05 — Final submission
As the student, I want all Capstone artifacts submitted, so that I receive credit.
GitHub link, deployed URL, Trello link, design doc link, demo video link
All submitted via Quantic dashboard before July 12
---
Stretch (only if ahead of schedule)
Playwright E2E tests on critical user flows
Power BI integration (link the SQLite/Postgres for BI consumption)
Email digest to supervisor at end of shift
Operator can add comments to a shift
Mobile-responsive operator screens (currently desktop-only)

