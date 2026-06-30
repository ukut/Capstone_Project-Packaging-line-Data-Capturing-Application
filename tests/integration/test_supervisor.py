"""Integration tests for B-02: operator close, supervisor dashboard/review/approve/lock."""

from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.loss_event import LossEvent
from app.models.shift import Role, Shift, ShiftName, ShiftStatus, User
from app.services.auth_service import hash_password


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    op = User(username="operator1", password_hash=hash_password("operator1"), role=Role.OPERATOR)
    sup = User(username="super1", password_hash=hash_password("super1"), role=Role.SUPERVISOR)
    admin = User(username="admin", password_hash=hash_password("admin"), role=Role.ADMIN)
    db.add_all([op, sup, admin])
    db.flush()

    sku = SKU(code="Brew Lager(33cl)")
    machine = Machine(name="FillerCrowner")
    bcs = BCSCategory(code="Breakdown")
    lt = LossType(code="Breakdown", suggested_bcs_code="Breakdown")
    db.add_all([sku, machine, bcs, lt])
    db.flush()

    # An OPEN shift owned by operator1 (for the close flow).
    open_shift = Shift(
        shift_date=date(2026, 6, 20),
        shift_name=ShiftName.A,
        line="Line 1",
        operator_id=op.id,
        status=ShiftStatus.OPEN,
    )
    # A PENDING shift with a 45-min event (for review/approve/lock).
    pending_shift = Shift(
        shift_date=date(2026, 6, 21),
        shift_name=ShiftName.B,
        line="Line 1",
        operator_id=op.id,
        status=ShiftStatus.PENDING_REVIEW,
    )
    db.add_all([open_shift, pending_shift])
    db.flush()
    db.add(
        LossEvent(
            shift_id=pending_shift.id,
            event_date=date(2026, 6, 21),
            event_start=time(7, 0),
            event_stop=time(7, 45),
            sku_id=sku.id,
            machine_id=machine.id,
            bcs_category_id=bcs.id,
            loss_type_id=lt.id,
            created_by_id=op.id,
        )
    )
    db.commit()
    ids = {"open": open_shift.id, "pending": pending_shift.id}
    db.close()
    yield ids


def _client() -> TestClient:
    return TestClient(app)


def _login(c, username):
    c.post("/login", data={"username": username, "password": username})


def _status(shift_id):
    db = SessionLocal()
    s = db.get(Shift, shift_id)
    st = s.status
    db.close()
    return st


# ----- access control -----


def test_dashboard_redirects_anonymous():
    c = _client()
    r = c.get("/supervisor", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/login")


def test_operator_forbidden_from_supervisor(setup_db):
    c = _client()
    _login(c, "operator1")
    r = c.get("/supervisor")
    assert r.status_code == 403


def test_supervisor_sees_dashboard(setup_db):
    c = _client()
    _login(c, "super1")
    r = c.get("/supervisor")
    assert r.status_code == 200
    assert "Supervisor Review" in r.text
    assert "Pending review" in r.text


# ----- review -----


def test_review_page_shows_event_and_anomaly(setup_db):
    c = _client()
    _login(c, "super1")
    r = c.get(f"/supervisor/shift/{setup_db['pending']}")
    assert r.status_code == 200
    assert "FillerCrowner" in r.text  # the event rendered
    assert "long_breakdown" in r.text  # the 45-min anomaly flagged


def test_review_missing_shift_404(setup_db):
    c = _client()
    _login(c, "super1")
    r = c.get("/supervisor/shift/9999")
    assert r.status_code == 404


# ----- approve / lock -----


def test_approve_then_lock_flow(setup_db):
    c = _client()
    _login(c, "super1")
    pid = setup_db["pending"]

    r1 = c.post(f"/supervisor/shift/{pid}/approve", follow_redirects=False)
    assert r1.status_code == 303
    assert _status(pid) == ShiftStatus.APPROVED

    r2 = c.post(f"/supervisor/shift/{pid}/lock", follow_redirects=False)
    assert r2.status_code == 303
    assert _status(pid) == ShiftStatus.LOCKED


def test_approve_open_shift_shows_error(setup_db):
    c = _client()
    _login(c, "super1")
    # The OPEN shift can't be approved -> error banner, status unchanged.
    r = c.post(f"/supervisor/shift/{setup_db['open']}/approve")
    assert r.status_code == 200
    assert "only a pending shift can be approved" in r.text
    assert _status(setup_db["open"]) == ShiftStatus.OPEN


def test_lock_before_approve_shows_error(setup_db):
    c = _client()
    _login(c, "super1")
    r = c.post(f"/supervisor/shift/{setup_db['pending']}/lock")
    assert r.status_code == 200
    assert "only an approved shift can be locked" in r.text
    assert _status(setup_db["pending"]) == ShiftStatus.PENDING_REVIEW


# ----- operator close -----


def test_operator_close_moves_shift_to_pending(setup_db):
    c = _client()
    _login(c, "operator1")
    oid = setup_db["open"]
    r = c.post(f"/operator/shift/{oid}/close", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/operator/shifts"
    assert _status(oid) == ShiftStatus.PENDING_REVIEW


def test_closed_shift_entry_is_read_only(setup_db):
    c = _client()
    _login(c, "operator1")
    # The pending shift's entry form should be read-only.
    r = c.get(f"/operator/shift/{setup_db['pending']}/entry")
    assert r.status_code == 200
    assert "read-only" in r.text


def test_supervisor_cannot_close_others_shift(setup_db):
    # super1 has operator access but isn't the owner -> forbidden.
    c = _client()
    _login(c, "super1")
    r = c.post(f"/operator/shift/{setup_db['open']}/close")
    assert r.status_code == 403
    assert _status(setup_db["open"]) == ShiftStatus.OPEN
