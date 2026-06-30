"""Review service — the supervisor's read-and-decide layer.

This service composes data the supervisor needs and applies the two review
transitions:

    dashboard()        -> shifts grouped Pending / Approved / Locked, each with
                          total downtime, event count, and anomaly count
    get_review(id)     -> one shift's events (with derived durations) plus the
                          anomalies the rule engine flags
    approve(shift, by) -> PENDING_REVIEW -> APPROVED
    lock(shift, by)    -> APPROVED -> LOCKED

Anomalies are *computed at review time*, never stored: the rule set can change
(Strategy pattern, Open/Closed) without a migration, and re-reviewing always
reflects the current rules. Each loss event's duration is derived (not a column)
so we wrap events in a small EventForReview that exposes exactly the three
attributes the rules read — id, machine_id, duration_minutes — keeping the rule
engine decoupled from the ORM.

Transitions raise InvalidShiftTransitionError (defined in ShiftService) on an
illegal state change, so operator-side and supervisor-side lifecycle errors are
reported identically.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.loss_event import LossEvent
from app.models.shift import Shift, ShiftStatus
from app.repositories.loss_event_repo import LossEventRepository
from app.repositories.shift_repo import ShiftRepository
from app.services.anomaly import ALL_RULES, Anomaly
from app.services.derived import DerivedFields, derive_fields
from app.services.shift_service import InvalidShiftTransitionError


@dataclass
class EventForReview:
    """A loss event prepared for review.

    Exposes id, machine_id, and duration_minutes (the attributes the anomaly
    rules read) alongside the original ORM event and its derived fields for the
    template.
    """

    id: int
    machine_id: int
    duration_minutes: int
    event: LossEvent
    derived: DerivedFields


@dataclass
class ShiftSummary:
    """One row on the supervisor dashboard."""

    shift: Shift
    operator_username: str
    event_count: int
    total_downtime_minutes: int
    anomaly_count: int


@dataclass
class ReviewDetail:
    """Everything the review screen for a single shift needs."""

    shift: Shift
    rows: list[EventForReview]
    anomalies: list[Anomaly]
    total_downtime_minutes: int = 0
    can_approve: bool = False
    can_lock: bool = False
    can_edit: bool = field(default=False)


# Statuses shown on the dashboard, in display order.
DASHBOARD_GROUPS: list[ShiftStatus] = [
    ShiftStatus.PENDING_REVIEW,
    ShiftStatus.APPROVED,
    ShiftStatus.LOCKED,
]


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.shifts = ShiftRepository(db)
        self.events = LossEventRepository(db)

    # ----- composition helpers -----

    def _events_for(self, shift: Shift) -> list[EventForReview]:
        out: list[EventForReview] = []
        for e in self.events.list_for_shift(shift.id):
            d = derive_fields(e.event_date, e.event_start, e.event_stop)
            out.append(
                EventForReview(
                    id=e.id,
                    machine_id=e.machine_id,
                    duration_minutes=d.duration_minutes,
                    event=e,
                    derived=d,
                )
            )
        return out

    def _anomalies_for(self, shift: Shift, events: list[EventForReview]) -> list[Anomaly]:
        context = {"shift": shift, "loss_events": events}
        anomalies: list[Anomaly] = []
        for rule in ALL_RULES:
            anomalies.extend(rule.evaluate(context))
        return anomalies

    # ----- reads -----

    def dashboard(self) -> dict[str, list[ShiftSummary]]:
        """Return shift summaries grouped by status for the dashboard."""
        grouped: dict[str, list[ShiftSummary]] = {}
        for status in DASHBOARD_GROUPS:
            summaries: list[ShiftSummary] = []
            for shift in self.shifts.list_by_status(status):
                events = self._events_for(shift)
                total = sum(e.duration_minutes for e in events)
                anomalies = self._anomalies_for(shift, events)
                summaries.append(
                    ShiftSummary(
                        shift=shift,
                        operator_username=shift.operator.username if shift.operator else "—",
                        event_count=len(events),
                        total_downtime_minutes=total,
                        anomaly_count=len(anomalies),
                    )
                )
            grouped[status.value] = summaries
        return grouped

    def get_review(self, shift_id: int) -> ReviewDetail | None:
        shift = self.shifts.get(shift_id)
        if shift is None:
            return None
        rows = self._events_for(shift)
        anomalies = self._anomalies_for(shift, rows)
        return ReviewDetail(
            shift=shift,
            rows=rows,
            anomalies=anomalies,
            total_downtime_minutes=sum(r.duration_minutes for r in rows),
            can_approve=shift.status == ShiftStatus.PENDING_REVIEW,
            can_lock=shift.status == ShiftStatus.APPROVED,
            can_edit=shift.status == ShiftStatus.OPEN,
        )

    # ----- transitions -----

    def approve(self, shift: Shift, supervisor_id: int) -> Shift:
        """PENDING_REVIEW -> APPROVED. Records who approved and when."""
        if shift.status != ShiftStatus.PENDING_REVIEW:
            raise InvalidShiftTransitionError(
                f"Shift {shift.id} is {shift.status.value}; only a pending shift can be approved."
            )
        shift.status = ShiftStatus.APPROVED
        shift.supervisor_id = supervisor_id
        shift.approved_at = datetime.now(UTC)
        self.shifts.commit()
        return shift

    def lock(self, shift: Shift, supervisor_id: int) -> Shift:
        """APPROVED -> LOCKED. After this, edits require an admin override."""
        if shift.status != ShiftStatus.APPROVED:
            raise InvalidShiftTransitionError(
                f"Shift {shift.id} is {shift.status.value}; only an approved shift can be locked."
            )
        shift.status = ShiftStatus.LOCKED
        if shift.supervisor_id is None:
            shift.supervisor_id = supervisor_id
        self.shifts.commit()
        return shift
