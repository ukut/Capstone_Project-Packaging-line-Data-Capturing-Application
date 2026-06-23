"""Loss-event service — business logic for entering a downtime event.

This is the heart of the three-tier design: the route handles HTTP, the
repository handles SQL, and THIS layer makes the decisions:

- enforce that you can only add events to an OPEN shift (not one already
  closed/approved/locked) — protects the supervisor's locked record
- compute and attach derived fields so the operator never types them
- record who created the event (audit)

Keeping these rules here (not in the route) means they apply identically no
matter how the event arrives, and they're unit-testable without a web server.
"""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.loss_event import LossEvent
from app.models.shift import Shift, ShiftStatus
from app.repositories.loss_event_repo import LookupRepository, LossEventRepository
from app.schemas.loss_event import LossEventCreate
from app.services.derived import derive_fields


class ShiftNotEditableError(Exception):
    """Raised when trying to add an event to a non-open shift."""


class InvalidEventTimingError(Exception):
    """Raised when start and stop are identical (zero-length event)."""


class LossEventService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = LossEventRepository(db)
        self.lookups = LookupRepository(db)

    def create_event(self, shift: Shift, payload: LossEventCreate, created_by_id: int) -> LossEvent:
        """Validate, apply business rules, persist, and return the new event."""
        # Rule 1: shift must be open for entry.
        if shift.status != ShiftStatus.OPEN:
            raise ShiftNotEditableError(
                f"Shift {shift.id} is {shift.status.value}; cannot add events."
            )

        # Rule 2: a zero-length event is meaningless. (Overnight events where
        # stop < start are valid — derive_fields treats stop as next-day.)
        if payload.event_start == payload.event_stop:
            raise InvalidEventTimingError("Event start and stop cannot be identical.")

        # Build the row from exactly the values the operator entered.
        event = LossEvent(
            shift_id=shift.id,
            event_date=payload.event_date,
            event_start=payload.event_start,
            event_stop=payload.event_stop,
            sku_id=payload.sku_id,
            machine_id=payload.machine_id,
            loss_type_id=payload.loss_type_id,
            bcs_category_id=payload.bcs_category_id,
            functional_failure_description=payload.functional_failure_description,
            failure_mode_description=payload.failure_mode_description,
            created_by_id=created_by_id,
            created_at=datetime.now(UTC),
        )

        self.events.add(event)
        self.events.commit()
        return event

    def derived_for(self, event: LossEvent) -> dict:
        """Return the computed columns for display/export (never stored)."""
        d = derive_fields(event.event_date, event.event_start, event.event_stop)
        return {
            "duration_hhmm": d.duration_hhmm,
            "duration_minutes": d.duration_minutes,
            "duration_hours": d.duration_hours,
            "month": d.month,
            "week": d.week,
            "year": d.year,
            "week_year": d.week_year,
            "month_year": d.month_year,
        }
