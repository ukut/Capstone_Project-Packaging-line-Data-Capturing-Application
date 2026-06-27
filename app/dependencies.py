"""Dependency injection helpers.

FastAPI's Depends() system is our DI container. This module centralizes:
- Database session injection (re-exported from database.py)
- Current-user resolution from the session cookie (B-01)
- Role-based access checks (B-01)

Routes import these from here, not from internal modules, so the wiring is easy
to mock in tests and the auth policy lives in one place.

Auth flow
---------
SessionMiddleware (wired in main.py) gives every request a signed `session`
dict. On login we store only `user_id` there; we never trust the cookie for
anything but that id, and re-load the user from the database on each request so
a deactivated account loses access immediately.

`get_optional_user` returns the user or None (for pages that render differently
when logged out, like the home page). `get_current_user` *requires* a user and
raises `AuthRequiredError`, which an exception handler turns into a redirect to
/login. `require_role(...)` builds a dependency that additionally checks role
and raises `ForbiddenError` (rendered as a 403 page).
"""

from collections.abc import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shift import Role, User
from app.repositories.user_repo import UserRepository

__all__ = [
    "get_db",
    "get_optional_user",
    "get_current_user",
    "require_role",
    "AuthRequiredError",
    "ForbiddenError",
]

SESSION_USER_KEY = "user_id"


class AuthRequiredError(Exception):
    """Raised when a login-required route is hit by an anonymous user.

    Carries the path the user was trying to reach so the handler can send them
    back there after a successful login (`/login?next=...`).
    """

    def __init__(self, next_url: str = "/") -> None:
        self.next_url = next_url


class ForbiddenError(Exception):
    """Raised when a logged-in user lacks the role a route requires."""

    def __init__(self, detail: str = "You don't have access to that page.") -> None:
        self.detail = detail


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Return the logged-in user, or None if there is no valid session.

    If the session points at a missing or deactivated user, the stale id is
    cleared so the cookie self-heals.
    """
    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        return None
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        request.session.pop(SESSION_USER_KEY, None)
        return None
    return user


def get_current_user(
    request: Request, user: User | None = Depends(get_optional_user)
) -> User:
    """Require an authenticated user. Redirects to /login if absent."""
    if user is None:
        raise AuthRequiredError(next_url=request.url.path)
    return user


def require_role(*roles: Role) -> Callable[..., User]:
    """Build a dependency that requires the current user to hold one of `roles`.

    Usage:
        @router.get("/admin/...")
        def view(user: User = Depends(require_role(Role.ADMIN))): ...
    """

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise ForbiddenError()
        return user

    return _checker
