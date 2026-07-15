# Bottling Line Data Capture System

A web-based operator data capture and supervisor review system for bottling line production tracking — replacing paper / Excel logs in food and beverage manufacturing.

**Real-world context:** Built to replace manual Excel logs at a brewery bottling line. Operators enter shift data (production counts, downtime, quality checks, material usage) via desktop browser in the control room. Supervisors review, flag anomalies, and approve shifts from the office. Approved data exports to legacy Excel format for downstream consumers.

**Capstone context:** This repository contains the public version of the system with **synthetic data only** — see `scripts/seed_synthetic.py`. The production deployment with real brewery data runs on a private intranet and is not in scope for this repository.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Type hints, modern async support |
| Web framework | FastAPI | Async, type-safe, auto-generated OpenAPI docs |
| Templates | Jinja2 + HTMX | Server-rendered with progressive interactivity, no SPA complexity |
| Database | SQLite (dev/Render) / PostgreSQL-ready | Zero-config for the demo; repository pattern allows DB swap |
| ORM | SQLAlchemy 2.0 | Industry standard, mature |
| Auth | bcrypt + session cookies | Proven, simple, no external dependencies |
| Testing | pytest + httpx | Standard Python stack |
| CI/CD | GitHub Actions | Lint, test, build on every push |
| Deployment | Render (demo) / Docker (intranet) | Free tier covers demo; Docker for on-prem |

## Architecture

Three-tier separation enforced by directory structure:

```
Routes (presentation)  →  Services (business logic)  →  Repositories (data access)  →  Database
```

See `docs/DESIGN.md` for design and architectural pattern decisions.

## Local development

```bash
# 1. Clone and enter
git clone <repo-url>
cd bottling-line-app

# 2. Create virtualenv and install
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 3. Configure environment
cp .env.example .env

# 4. Initialize database with synthetic seed data
python -m scripts.init_db
python -m scripts.seed_synthetic

# 5. Run
uvicorn app.main:app --reload

# Visit http://localhost:8000
# Demo accounts (operator1 / super1 / admin) — see "Demo accounts" below
```

## Demo accounts

The seed script (`scripts/seed.py`, run automatically on each Render deploy) creates three demo users so the role-based access can be evaluated end to end:

| Username | Password | Role |
|---|---|---|
| `operator1` | `operator1` | operator |
| `super1` | `super1` | supervisor |
| `admin` | `admin` | admin |

These are **demo-only credentials** for the public capstone deployment — username deliberately equals password purely to make evaluation frictionless. Passwords are bcrypt-hashed at rest regardless, and the production intranet deployment uses real per-user credentials (out of scope for this repository).

## Running tests

```bash
pytest                          # All tests
pytest tests/unit               # Unit only
pytest tests/integration        # Integration only
pytest --cov=app                # With coverage
```

## Project layout

```
app/
├── main.py              # FastAPI app entry, middleware, lifespan
├── config.py            # Settings via pydantic-settings
├── database.py          # SQLAlchemy engine + session factory
├── dependencies.py      # FastAPI dependency injection wiring
├── models/              # SQLAlchemy ORM models
├── repositories/        # Data access layer (Repository pattern)
├── services/            # Business logic
│   └── anomaly/         # Anomaly detection rules (Strategy pattern)
├── routes/              # FastAPI routers — presentation layer
├── schemas/             # Pydantic request/response models
├── templates/           # Jinja2 HTML templates
└── static/              # CSS, minimal JS

scripts/
├── init_db.py           # Create schema
└── seed_synthetic.py    # Generate realistic synthetic data

tests/
├── unit/                # Pure-function tests
└── integration/         # API endpoint tests

docs/
├── DESIGN.md            # Design and testing document (Capstone deliverable)
├── USER_STORIES.md      # Product backlog
└── ARCHITECTURE.md      # System architecture notes
```

## Capstone deliverables

| Deliverable | Location |
|---|---|
| Code repository | This repo |
| Deployed version | https://bottling-line-demo.onrender.com |
| Task board | https://trello.com/invite/b/6a33d65ff1267c7a6aa8efbb/ATTI48a3fad6225e1b1e3b046a47ef355ddf71F50C8C/packaging-line-data-capture |
| Design and testing doc | `docs/DESIGN.md` |
| Demo recording | https://drive.google.com/file/d/1NBhxpWM6N4vSMfE_61w3V8bL4Wyo3xzp/view?usp=sharing

## License

Ini Ekpenyong Ukut.
