from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.shift import Role, Shift, ShiftName, ShiftStatus, User
from app.services.auth_service import hash_password

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    op = User(username="op1", password_hash=hash_password("op1"), role=Role.OPERATOR)
    db.add(op)
    db.flush()
    sku = SKU(code="Brew Lager(33cl)")
    machine = Machine(name="FillerCrowner")
    bcs_b = BCSCategory(code="Breakdown")
    bcs_p = BCSCategory(code="PlannedDownTime")
    lt = LossType(code="CILT", suggested_bcs_code="PlannedDownTime")
    db.add_all([sku, machine, bcs_b, bcs_p, lt])
    db.flush()
    shift = Shift(
        shift_date=date(2026, 6, 20),
        shift_name=ShiftName.A,
        operator_id=op.id,
        status=ShiftStatus.OPEN,
    )
    db.add(shift)
    db.commit()
    ids = dict(
        shift=shift.id, sku=sku.id, machine=machine.id, lt=lt.id, bcs_b=bcs_b.id, bcs_p=bcs_p.id
    )
    db.close()
    client.post(
        "/login",
        data={"username": "op1", "password": "op1"},
        follow_redirects=False,
    )
    yield ids
    client.cookies.clear()


def test_entry_form_renders(setup_db):
    r = client.get(f"/operator/shift/{setup_db['shift']}/entry")
    assert r.status_code == 200
    assert "Downtime / Loss Event Entry" in r.text
    assert "Brew Lager(33cl)" in r.text  # SKU dropdown populated
    assert "FillerCrowner" in r.text  # machine dropdown populated


def test_submit_event_creates_and_lists(setup_db):
    r = client.post(
        f"/operator/shift/{setup_db['shift']}/entry",
        data={
            "event_date": "2026-06-20",
            "event_start": "07:00",
            "event_stop": "08:00",
            "sku_id": setup_db["sku"],
            "machine_id": setup_db["machine"],
            "loss_type_id": setup_db["lt"],
            "bcs_category_id": setup_db["bcs_b"],
            "functional_failure_description": "Lift cylinder dropped",
            "failure_mode_description": "Loose bolt",
        },
    )
    assert r.status_code == 200
    assert "1:00 (60m)" in r.text  # derived duration shown
    assert "Lift cylinder dropped" in r.text
    assert "Events this shift (1)" in r.text


def test_bcs_suggestion_preselects(setup_db):
    # CILT suggests PlannedDownTime -> that option should be 'selected'
    r = client.get(f"/operator/loss-type/{setup_db['lt']}/bcs")
    assert r.status_code == 200
    assert "selected" in r.text
    assert "PlannedDownTime" in r.text


def test_identical_start_stop_rejected(setup_db):
    r = client.post(
        f"/operator/shift/{setup_db['shift']}/entry",
        data={
            "event_date": "2026-06-20",
            "event_start": "07:00",
            "event_stop": "07:00",
            "sku_id": setup_db["sku"],
            "machine_id": setup_db["machine"],
            "loss_type_id": setup_db["lt"],
            "bcs_category_id": setup_db["bcs_b"],
        },
    )
    assert r.status_code == 200
    assert "cannot be identical" in r.text


def test_cannot_add_to_closed_shift(setup_db):
    db = SessionLocal()
    sh = db.get(Shift, setup_db["shift"])
    sh.status = ShiftStatus.APPROVED
    db.commit()
    db.close()
    r = client.post(
        f"/operator/shift/{setup_db['shift']}/entry",
        data={
            "event_date": "2026-06-20",
            "event_start": "07:00",
            "event_stop": "08:00",
            "sku_id": setup_db["sku"],
            "machine_id": setup_db["machine"],
            "loss_type_id": setup_db["lt"],
            "bcs_category_id": setup_db["bcs_b"],
        },
    )
    assert "cannot add events" in r.text.lower()
