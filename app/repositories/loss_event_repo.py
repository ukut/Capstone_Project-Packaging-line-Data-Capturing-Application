"""Repositories for loss events and the lookup tables.

Repository pattern: the ONLY place that talks to the database for these
entities. Services call these methods; they never write SQLAlchemy queries
directly. This is what lets us swap SQLite for PostgreSQL later by changing
only DATABASE_URL, and what lets tests substitute fakes.
"""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.loss_event import LossEvent


class LookupRepository:
    """Read access to the four reference tables that fill the dropdowns."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def active_skus(self) -> Sequence[SKU]:
        return self.db.execute(select(SKU).where(SKU.is_active).order_by(SKU.code)).scalars().all()

    def active_machines(self) -> Sequence[Machine]:
        return (
            self.db.execute(select(Machine).where(Machine.is_active).order_by(Machine.name))
            .scalars()
            .all()
        )

    def active_loss_types(self) -> Sequence[LossType]:
        return (
            self.db.execute(select(LossType).where(LossType.is_active).order_by(LossType.code))
            .scalars()
            .all()
        )

    def active_bcs_categories(self) -> Sequence[BCSCategory]:
        return (
            self.db.execute(
                select(BCSCategory).where(BCSCategory.is_active).order_by(BCSCategory.code)
            )
            .scalars()
            .all()
        )

    def bcs_by_code_map(self) -> dict[str, BCSCategory]:
        """For the suggestion service: code -> BCSCategory."""
        return {b.code: b for b in self.active_bcs_categories()}

    def get_loss_type(self, loss_type_id: int) -> LossType | None:
        return self.db.get(LossType, loss_type_id)


class LossEventRepository:
    """Create and read loss events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: LossEvent) -> LossEvent:
        self.db.add(event)
        self.db.flush()  # assign PK without committing yet
        return event

    def list_for_shift(self, shift_id: int) -> Sequence[LossEvent]:
        return (
            self.db.execute(
                select(LossEvent)
                .where(LossEvent.shift_id == shift_id)
                .order_by(LossEvent.event_start)
            )
            .scalars()
            .all()
        )

    def commit(self) -> None:
        self.db.commit()
