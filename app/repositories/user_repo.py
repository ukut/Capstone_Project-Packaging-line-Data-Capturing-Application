"""User repository — data access for the user table.

Repository pattern: the only module that queries `user`. Services (auth, and
later admin user-management) call these methods; routes never touch the ORM
directly. Keeping it tiny is fine — it grows as user stories need it.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shift import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.execute(select(User).where(User.username == username)).scalars().first()
