"""Shift service — business logic for the shift lifecycle.

open_shift() implements the 'resume if one exists, else create' rule that keeps
a single operator from fragmenting their work across duplicate shift records.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.shift import Shift, ShiftStatus
from app.repositories.shift_repo import ShiftRepository
from app.schemas.shift import ShiftCreate


class ShiftService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shifts = ShiftRepository(db)

    def open_shift(self, payload: ShiftCreate, operator_id: int) -> Shift:
        """Open a shift for the operator, resuming an existing one if present.

        Resolution order:
        1. If a shift already exists for this operator/date/name, return it
           (resume — whatever its status; the entry form enforces edit rules).
        2. Otherwise create a new OPEN shift.
        """
        existing = self.shifts.find_for_operator_on_date(
            operator_id, payload.shift_date, payload.shift_name
        )
        if existing is not None:
            return existing

        shift = Shift(
            shift_date=payload.shift_date,
            shift_name=payload.shift_name,
            line=payload.line,
            operator_id=operator_id,
            status=ShiftStatus.OPEN,
            opened_at=datetime.now(UTC),
        )
        self.shifts.add(shift)
        self.shifts.commit()
        return shift
