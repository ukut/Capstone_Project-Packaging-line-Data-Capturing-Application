"""Shift repository — data access for the shift lifecycle.

Repository pattern: the only place that queries the shift table. The service
calls these methods; routes never touch SQLAlchemy directly.
"""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shift import Shift, ShiftStatus


class ShiftRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, shift_id: int) -> Shift | None:
        return self.db.get(Shift, shift_id)

    def find_open_for_operator(self, operator_id: int) -> Shift | None:
        """Return the operator's currently-open shift, if any.

        Supports the 'one open shift per operator' rule: starting a shift when
        one is already open resumes it instead of creating a duplicate.
        """
        return (
            self.db.execute(
                select(Shift)
                .where(Shift.operator_id == operator_id, Shift.status == ShiftStatus.OPEN)
                .order_by(Shift.opened_at.desc())
            )
            .scalars()
            .first()
        )

    def find_for_operator_on_date(
        self, operator_id: int, shift_date: date, shift_name
    ) -> Shift | None:
        """Find an existing shift matching operator + date + name (any status)."""
        return (
            self.db.execute(
                select(Shift).where(
                    Shift.operator_id == operator_id,
                    Shift.shift_date == shift_date,
                    Shift.shift_name == shift_name,
                )
            )
            .scalars()
            .first()
        )

    def list_for_operator(self, operator_id: int) -> Sequence[Shift]:
        return (
            self.db.execute(
                select(Shift)
                .where(Shift.operator_id == operator_id)
                .order_by(Shift.shift_date.desc(), Shift.opened_at.desc())
            )
            .scalars()
            .all()
        )

    def list_by_status(self, *statuses: ShiftStatus) -> Sequence[Shift]:
        """Return shifts in any of the given statuses, newest first.

        Used by the supervisor dashboard to show Pending / Approved / Locked
        groups. Passing no statuses returns every shift.
        """
        stmt = select(Shift)
        if statuses:
            stmt = stmt.where(Shift.status.in_(statuses))
        stmt = stmt.order_by(Shift.shift_date.desc(), Shift.opened_at.desc())
        return self.db.execute(stmt).scalars().all()

    def add(self, shift: Shift) -> Shift:
        self.db.add(shift)
        self.db.flush()
        return shift

    def commit(self) -> None:
        self.db.commit()
