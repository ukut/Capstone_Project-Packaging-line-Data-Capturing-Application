"""Repository pattern: abstract data access behind a stable interface.

WHY this pattern (for the design document):
- Services depend on repositories, never on SQLAlchemy directly.
- Swapping SQLite for PostgreSQL touches only DATABASE_URL — no service code changes.
- Tests substitute in-memory or mock repositories without touching real DB.
- Future move to async / different ORM is a single-layer change.

Every concrete repository (UserRepository, ShiftRepository, etc.) inherits
this generic base for the standard CRUD; domain-specific queries are added
as methods on the subclass.
"""

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic CRUD repository. Subclass with the model type."""

    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, *, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        return self.db.execute(stmt).scalars().all()

    def add(self, entity: ModelT) -> ModelT:
        self.db.add(entity)
        self.db.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.db.delete(entity)
        self.db.flush()

    def commit(self) -> None:
        self.db.commit()
