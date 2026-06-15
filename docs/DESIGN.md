# Design and Testing Document

**Project:** Bottling Line Data Capture System
**Author:** Ini Ukut
**Programme:** Quantic MSc Software Engineering — Capstone
**Last updated:** _(update as you go)_

---

## 1. Project overview

### 1.1 Problem statement

Bottling line operators at food and beverage manufacturers currently capture production data (counts, downtime events, quality checks, material usage) on paper or in shared Excel workbooks. This workflow produces inconsistent data — free-text reasons that resist analysis, missed entries, errors caught only after the shift, and no audit trail of who entered or modified each value. Supervisors spend hours validating and reconciling data that should have been correct at entry.

### 1.2 Solution

A web-based data capture system in which a single operator per shift enters production data through validated forms in the control-room browser, and a supervisor reviews, flags anomalies, and approves the shift from any other browser on the intranet. Approved data is immutable, fully audited, and exportable in the legacy Excel format so downstream consumers are unaffected.

### 1.3 Users and roles

| Role | Primary tasks |
|---|---|
| **Admin** | User management, lookup table CRUD (SKUs, downtime reasons, machines, reject categories) |
| **Operator** | Shift entry — production, downtime, quality, materials |
| **Supervisor** | Review entered data, see flagged anomalies, approve / lock the shift, export to Excel |

---

## 2. Technology and architectural decisions

### 2.1 Language and framework

**Decision:** Python 3.11+ with FastAPI.

**Reasoning:** Python is the team's primary language and is well-supported on both the brewery's intranet PCs and on Render's free tier. FastAPI provides type-checked request/response models via Pydantic (catching a class of bugs at startup rather than at first request), async support if needed later, and an auto-generated OpenAPI schema useful for both internal debugging and any future system-to-system integration.

Alternatives considered: Flask (less type safety, no built-in async, no automatic OpenAPI); Django (heavier than needed for a single-purpose app, would have meant fighting the ORM for our schema preferences).

### 2.2 Database

**Decision:** SQLite for both development and the Capstone demo deployment; PostgreSQL-ready via the Repository pattern.

**Reasoning:** With one operator per shift, write contention is non-existent — SQLite easily handles the load and removes an entire class of operational complexity (no DB server to provision, monitor, or back up beyond copying a single file). For the Capstone demo on Render's free tier, SQLite avoids the cost and connection-management overhead of an external DB. The repository pattern (see §3) ensures that swapping to PostgreSQL later requires changing only `DATABASE_URL`, with no code changes.

### 2.3 Templating

**Decision:** Server-rendered Jinja2 templates with HTMX for progressive interactivity.

**Reasoning:** Operators use desktop browsers in a controlled environment — a full SPA (React, Vue) would add build complexity, larger payloads, and more potential failure modes for no user benefit. HTMX gives us partial-page updates (e.g., adding a downtime row without a full reload) using server-rendered HTML, keeping the application's source of truth on the server.

### 2.4 Authentication

**Decision:** Username + bcrypt-hashed password, session cookies via `itsdangerous`.

**Reasoning:** The application runs on a controlled intranet — the threat model does not require OAuth or SSO. bcrypt is the industry standard for password hashing; session cookies (HTTP-only, `SameSite=lax`, HTTPS-only in production) avoid the complexity and revocation problems of JWTs for a non-distributed application.

### 2.5 Deployment

**Decision:** Dual-target: Docker container for brewery intranet, Render free tier for Capstone graders.

**Reasoning:** The brewery requires on-premises deployment for data sovereignty; the Capstone requires a publicly accessible demo. The same codebase serves both — only environment variables and the seeded data differ. Cost: intranet deployment is one-time setup on an existing PC (no incremental cost); Render free tier is $0/month for the demo.

---

## 3. Software design patterns used

The following patterns are applied with clear reasons, not as a checklist:

### 3.1 Three-tier architecture

Routes (`app/routes/`) handle HTTP request/response and template rendering. Services (`app/services/`) hold business logic — shift lifecycle, validation rules, anomaly evaluation, export. Repositories (`app/repositories/`) wrap all database access.

**Why:** Each layer is independently testable. Business logic doesn't know about HTTP; data access doesn't know about the web framework. Replacing the web layer (e.g., adding a CLI) or the data layer (e.g., switching to PostgreSQL) touches only one tier.

### 3.2 Repository pattern

A generic `BaseRepository[ModelT]` provides CRUD; concrete repositories (`UserRepository`, `ShiftRepository`, etc.) add domain-specific queries.

**Why:** Services depend on the repository's interface, not SQLAlchemy. Tests substitute fake/in-memory repositories without touching a real database. Migration to PostgreSQL (or a future async ORM) is a single-layer change.

### 3.3 Strategy pattern (anomaly detection)

`AnomalyRule` is an abstract base; each concrete rule (`LongDowntimeRule`, `HighRejectRateRule`, ...) implements `evaluate(shift_context)`. The supervisor service iterates a registered list of rules.

**Why:** Adding a new anomaly rule means writing one new class and registering it — no edits to existing code (Open/Closed Principle). Each rule is unit-testable in isolation. Rules can be enabled, disabled, or reconfigured per environment via settings.

### 3.4 Dependency injection (via FastAPI's `Depends`)

Database sessions, current user, and role checks are injected into routes via `Depends(...)`.

**Why:** Test fixtures override `Depends` to supply test databases or fake users without modifying route code. Production code is free of `if testing then ... else ...` branches.

### 3.5 Service layer

A thin layer between routes and repositories where business decisions live — e.g., "closing a shift triggers anomaly evaluation, writes to the audit log, and emits a notification."

**Why:** Routes stay small and focused on HTTP concerns. Business logic can be reused across HTTP, future CLI, or future scheduled jobs.

### 3.6 Factory function (`create_app`)

The FastAPI app is built inside `create_app()` rather than constructed at module top-level.

**Why:** Tests construct a fresh app with overridden config; future deployments could swap in different middleware or routes per environment.

---

## 4. Database schema

_(Populated at end of Sprint 1, after deriving from the real Excel workbook structure. Will include an ER diagram, table list, and key constraints.)_

---

## 5. Testing strategy

### 5.1 Test pyramid

| Layer | Tool | Scope | Target |
|---|---|---|---|
| Unit | pytest | Pure-function logic — validation rules, anomaly rules, calculations | ≥ 80% coverage |
| Integration | pytest + httpx TestClient | API endpoints with a real in-memory SQLite DB | Critical paths |
| Manual exploratory | Browser | Pre-release verification of full operator + supervisor workflows | End of each sprint |

End-to-end tests with Playwright were considered but deprioritized: the integration tests cover the API surface, and manual exploratory testing of the UI is feasible given the small page count.

### 5.2 What we explicitly test

**Anomaly rules (Strategy pattern):** Each rule has tests covering the firing case, the silent case, the boundary, and an edge case (empty input). See `tests/unit/test_anomaly_rules.py`.

**Validation logic:** Every Pydantic schema field with constraints is tested against valid and invalid inputs.

**Authentication:** Login flow, session expiration, role-based access denial.

**Shift lifecycle:** Open → entries → close → review → approve → lock — each transition tested.

**Excel export:** Generated workbook matches the legacy column layout, formula cells included where required.

### 5.3 Continuous integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and PR:

1. `ruff check` — linting
2. `ruff format --check` — formatting consistency
3. `pytest --cov=app` — test suite with coverage report
4. Matrix across Python 3.11 and 3.12 to catch version-specific issues

A PR cannot be merged if CI fails (branch protection rule on `main`).

### 5.4 What the existing test suite proves (Sprint 0)

- App boots cleanly
- Health endpoint responds
- Landing page renders
- OpenAPI schema is generated
- Anomaly Strategy pattern works end-to-end with fake data

Sprint 1+ adds tests as features land.

---

## 6. Deployment

### 6.1 Capstone demo (Render free tier)

`render.yaml` declares the service. On every push to `main`, Render rebuilds, runs `init_db` and `seed_synthetic`, and starts uvicorn. Free tier sleeps after 15 min of inactivity — first request after sleep takes ~30 sec to wake. This is documented in the README and acceptable for grader use.

### 6.2 Brewery intranet (Docker)

A `Dockerfile` builds a single image runnable on any internal Linux host. The brewery's IT runs it as a systemd service bound to the intranet IP. Data persists in a SQLite file on a network share, backed up nightly to a separate drive.

### 6.3 Cost analysis

| Environment | Compute | Storage | Monthly cost |
|---|---|---|---|
| Render demo | Free tier (shared, sleeps) | Ephemeral SQLite, reseeded on deploy | $0 |
| Brewery intranet | Existing on-prem PC | Existing network share | $0 incremental |

For a production rollout to multiple breweries, a $25/month Render Standard plan (or a comparable PostgreSQL-backed deployment) would lift the sleep restriction and add a managed database.

---

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Operator resistance to leaving Excel | UI mirrors familiar shift layout; one-shift parallel run alongside Excel before cutover |
| Network outage at brewery | SQLite is local; app continues to work; data syncs to network backup when restored |
| Render free tier sleeps mid-demo | Pre-warm by visiting URL 30 sec before grader recording |
| Schema discovered to be wrong mid-sprint | Repository pattern isolates schema changes; migrations via Alembic in Sprint 2+ |

---

## 8. Repository and project management

- **GitHub repo:** _(link)_ — shared with `quantic-grader`
- **Trello board:** _(link)_ — backlog organized by sprint, columns: Backlog / In Progress / In Review / Done
- **Sprint cadence:** 2 weeks per sprint, 3 sprints + foundation week + submission week
- **Branching:** `main` (protected, demo deploys from here), `develop`, feature branches `feat/<story-id>-<slug>`
- **Code review:** every PR reviewed before merge (self-review documented in commit messages for the solo project)

---

## 9. Demo deployment link

_(Filled in end of Sprint 1)_

