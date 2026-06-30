"""Shift service — business logic for the shift lifecycle.

open_shift() implements the 'resume if one exists, else create' rule that keeps
a single operator from fragmenting their work across duplicate shift records.

submit_for_review() is the operator's hand-off: it moves an OPEN shift to
PENDING_REVIEW so a supervisor can review it. After this point the loss-event
service refuses new events (it only accepts OPEN shifts), so the data the
supervisor sees can't change underneath them.

The supervisor-side transitions (approve, lock) live in ReviewService, but they
raise the same InvalidShiftTransitionError defined here so every illegal state
change is reported the same way.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.shift import Shift, ShiftStatus
from app.repositories.shift_repo import ShiftRepository
from app.schemas.shift import ShiftCreate


class InvalidShiftTransitionError(Exception):
    """Raised when a shift is moved between states in a way the lifecycle forbids.

    e.g. submitting a shift that isn't OPEN, or approving one that isn't
    PENDING_REVIEW. Carries a human-readable message for the UI.
    """


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

    def submit_for_review(self, shift: Shift) -> Shift:
        """Move an OPEN shift to PENDING_REVIEW (the operator's 'close shift').

        Only OPEN shifts can be submitted; anything else is already in or past
        review, so re-submitting would be meaningless (and could clobber a
        supervisor's approval).
        """
        if shift.status != ShiftStatus.OPEN:
            raise InvalidShiftTransitionError(
                f"Shift {shift.id} is {shift.status.value}; only an open shift can be submitted."
            )
        shift.status = ShiftStatus.PENDING_REVIEW
        shift.closed_at = datetime.now(UTC)
        self.shifts.commit()
        return shift
