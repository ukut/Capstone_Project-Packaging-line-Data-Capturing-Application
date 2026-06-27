"""Authentication service — password hashing/verification and credential checks.

Two layers live here:

1. Pure password functions (`hash_password`, `verify_password`) wrapping bcrypt.
   They're module-level so any caller — the seed script, an admin "create user"
   flow, this service — hashes and checks passwords the *same* way. Centralizing
   the algorithm here means a future change (cost factor, argon2) touches one
   place.

2. `AuthService.authenticate()` — the business rule for "may this username +
   password log in": the user must exist, be active, and the password must
   match. It deliberately returns the same failure for "no such user" and "wrong
   password" so the login screen can't be used to enumerate valid usernames.
"""

import bcrypt
from sqlalchemy.orm import Session

from app.models.shift import User
from app.repositories.user_repo import UserRepository


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if `password` matches the stored bcrypt `password_hash`.

    Returns False (rather than raising) on a malformed hash, so a bad/legacy row
    can never crash the login route — it simply fails to authenticate.
    """
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except (ValueError, TypeError):
        return False


class AuthService:
    """Business logic for authenticating a user."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def authenticate(self, username: str, password: str) -> User | None:
        """Return the User if credentials are valid and the account is active.

        Returns None for every failure mode (unknown user, inactive account,
        wrong password) — the caller shows one generic message either way.
        """
        user = self.users.get_by_username(username)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
