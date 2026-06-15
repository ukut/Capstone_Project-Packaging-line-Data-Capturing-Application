"""Dependency injection helpers.

FastAPI's Depends() system is our DI container. This module centralizes:
- Database session injection (re-exported from database.py)
- Current-user resolution (Sprint 1)
- Role-based access checks (Sprint 1)

Routes import dependencies from here, not from internal modules, so the
wiring is easy to mock in tests.
"""

from app.database import get_db

__all__ = ["get_db"]

# Sprint 1 additions:
# def get_current_user(...) -> User: ...
# def require_role(role: Role) -> Callable: ...
