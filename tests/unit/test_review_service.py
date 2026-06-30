"""Unit tests for the review service: transitions, anomalies, dashboard."""

from datetime import date, time

import pytest

from app.database import Base, SessionLocal, engine
from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.loss_event import LossEvent
from app.models.shift import Role, Shift, ShiftName, ShiftStatus, User
from app.services.review_service import ReviewService
from app.services.shift_service import InvalidShiftTransitionError, ShiftService


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


def _seed_lookups(db):
    sku = SKU(code="Brew Lager(33cl)")
    machine = Machine(name="FillerCrowner")
    bcs = BCSCategory(code="Breakdown")
    lt = LossType(code="Breakdown", suggested_bcs_code="Breakdown")
    db.add_all([sku, machine, bcs, lt])
    db.flush()
    return sku, machine, bcs, lt


def _make_shift(db, status=ShiftStatus.OPEN, operator=None):
    if operator is None:
        operator = User(username="op", password_hash="x", role=Role.OPERATOR)
        db.add(operator)
        db.flush()
    shift = Shift(
        shift_date=date(2026, 6, 20),
        shift_name=ShiftName.A,
        line="Line 1",
        operator_id=operator.id,
        status=status,
    )
    db.add(shift)
    db.flush()
    return shift


def _add_event(db, shift, lookups, start, stop):
    sku, machine, bcs, lt = lookups
    ev = LossEvent(
        shift_id=shift.id,
        event_date=date(2026, 6, 20),
        event_start=start,
        event_stop=stop,
        sku_id=sku.id,
        machine_id=machine.id,
        bcs_category_id=bcs.id,
        loss_type_id=lt.id,
        created_by_id=shift.operator_id,
    )
    db.add(ev)
    db.flush()
    return ev


# ----- transitions -----


def test_submit_for_review_open_to_pending():
    db = SessionLocal()
    shift = _make_shift(db, ShiftStatus.OPEN)
    db.commit()
    ShiftService(db).submit_for_review(shift)
    assert shift.status == ShiftStatus.PENDING_REVIEW
    assert shift.closed_at is not None
    db.close()


def test_submit_rejects_non_open():
    db = SessionLocal()
    shift = _make_shift(db, ShiftStatus.PENDING_REVIEW)
    db.commit()
    with pytest.raises(InvalidShiftTransitionError):
        ShiftService(db).submit_for_review(shift)
    db.close()


def test_approve_pending_to_approved():
    db = SessionLocal()
    sup = User(username="sup", password_hash="x", role=Role.SUPERVISOR)
    db.add(sup)
    db.flush()
    shift = _make_shift(db, ShiftStatus.PENDING_REVIEW)
    db.commit()
    ReviewService(db).approve(shift, supervisor_id=sup.id)
    assert shift.status == ShiftStatus.APPROVED
    assert shift.supervisor_id == sup.id
    assert shift.approved_at is not None
    db.close()


def test_approve_rejects_non_pending():
    db = SessionLocal()
    shift = _make_shift(db, ShiftStatus.OPEN)
    db.commit()
    with pytest.raises(InvalidShiftTransitionError):
        ReviewService(db).approve(shift, supervisor_id=1)
    db.close()


def test_lock_approved_to_locked():
    db = SessionLocal()
    shift = _make_shift(db, ShiftStatus.APPROVED)
    db.commit()
    ReviewService(db).lock(shift, supervisor_id=1)
    assert shift.status == ShiftStatus.LOCKED
    db.close()


def test_lock_rejects_non_approved():
    db = SessionLocal()
    shift = _make_shift(db, ShiftStatus.PENDING_REVIEW)
    db.commit()
    with pytest.raises(InvalidShiftTransitionError):
        ReviewService(db).lock(shift, supervisor_id=1)
    db.close()


# ----- anomalies / review detail -----


def test_get_review_flags_long_breakdown():
    db = SessionLocal()
    lookups = _seed_lookups(db)
    shift = _make_shift(db, ShiftStatus.PENDING_REVIEW)
    # 45-minute event -> LongBreakdownRule (threshold 30) fires.
    _add_event(db, shift, lookups, time(7, 0), time(7, 45))
    db.commit()

    detail = ReviewService(db).get_review(shift.id)
    assert detail is not None
    assert len(detail.rows) == 1
    assert detail.total_downtime_minutes == 45
    assert any(a.rule_name == "long_breakdown" for a in detail.anomalies)
    assert detail.can_approve is True
    assert detail.can_lock is False
    db.close()


def test_get_review_clean_shift_has_no_anomalies():
    db = SessionLocal()
    lookups = _seed_lookups(db)
    shift = _make_shift(db, ShiftStatus.PENDING_REVIEW)
    _add_event(db, shift, lookups, time(7, 0), time(7, 10))  # 10 min, clean
    db.commit()

    detail = ReviewService(db).get_review(shift.id)
    assert detail.anomalies == []
    db.close()


def test_get_review_missing_shift_returns_none():
    db = SessionLocal()
    assert ReviewService(db).get_review(999) is None
    db.close()


# ----- dashboard -----


def test_dashboard_groups_and_counts():
    db = SessionLocal()
    lookups = _seed_lookups(db)
    op = User(username="op", password_hash="x", role=Role.OPERATOR)
    db.add(op)
    db.flush()

    pending = _make_shift(db, ShiftStatus.PENDING_REVIEW, operator=op)
    _add_event(db, pending, lookups, time(7, 0), time(7, 45))  # 45 min, 1 anomaly
    _make_shift(db, ShiftStatus.APPROVED, operator=op)
    db.commit()

    groups = ReviewService(db).dashboard()
    assert len(groups["pending"]) == 1
    assert len(groups["approved"]) == 1
    assert groups["locked"] == []

    p = groups["pending"][0]
    assert p.operator_username == "op"
    assert p.event_count == 1
    assert p.total_downtime_minutes == 45
    assert p.anomaly_count >= 1
    db.close()
