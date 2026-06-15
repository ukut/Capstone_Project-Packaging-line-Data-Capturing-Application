# Architecture Notes

Companion to `DESIGN.md`. Lower-level / how-to-think-about-it notes for the developer.

## Request flow

```
Browser ─HTTP─▶ Uvicorn ─▶ FastAPI ─▶ SessionMiddleware ─▶ Router
                                                            │
                                                            ▼
                                                   Route handler
                                                            │
                       ┌────────────────────────────────────┘
                       ▼
                Service (business logic)
                       │
                       ▼
              Repository (data access)
                       │
                       ▼
                  SQLAlchemy
                       │
                       ▼
                    SQLite
```

Each layer only knows about the layer directly below it. Crossing layers (e.g., a route calling SQLAlchemy directly) is a code smell to call out in PR review.

## Where business rules live

| Rule | Lives in |
|---|---|
| "Field X must be between 0 and Y" | Pydantic schema |
| "A reject_count > 0 requires a reject_category" | Pydantic schema validator |
| "Closing a shift triggers anomaly evaluation" | `ShiftService.close()` |
| "Only the operator who opened a shift can edit it" | Route guard via `Depends` |
| "Approved shifts cannot be edited" | `ShiftService.assert_editable()` |
| "Anomaly: downtime > N minutes" | `LongDowntimeRule` (Strategy) |

## When to add a new endpoint vs. a new service method

If two routes do the same business action with different presentation (e.g., HTML form post vs. JSON API), they call the same service method. A service method has one job per "business verb" — open shift, close shift, approve shift, etc.

## Audit trail discipline

Anything that modifies operator-entered data writes to `audit_log` *before* the change commits. The audit entry includes: user_id, action, entity_type, entity_id, before_value (JSON), after_value (JSON), reason (required for edits, auto-set for system actions), timestamp.

The audit table is append-only. There is no delete or update on audit rows, even for admins.

## Migration story (SQLite → PostgreSQL)

If/when production volume exceeds SQLite's comfortable range:

1. Add Alembic for migrations (Sprint 2)
2. Change `DATABASE_URL` to a Postgres URL
3. Run migrations against the new DB
4. Restart the app

No application code changes — that's the repository pattern paying off.

## Things deliberately left out

- **OAuth / SSO** — overkill for intranet
- **Async DB** — single-operator workload doesn't benefit, adds complexity
- **GraphQL** — REST/HTMX is sufficient and simpler
- **Microservices** — premature; one process is enough
- **Kubernetes** — Docker on a single host is enough
- **Real-time WebSockets** — supervisor doesn't need live updates; refresh is fine
