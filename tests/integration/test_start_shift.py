import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.shift import Role, Shift, ShiftStatus, User


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = SessionLocal()
    db.add(User(username="operator1", password_hash="x", role=Role.OPERATOR))
    db.commit()
    db.close()
    yield


client = TestClient(app)


def test_new_shift_form_renders():
    r = client.get("/operator/shift/new")
    assert r.status_code == 200
    assert "Open a Shift" in r.text
    # shift name options present
    assert "DAY" in r.text or "A" in r.text


def test_open_shift_creates_and_redirects_to_entry():
    r = client.post(
        "/operator/shift/new",
        data={"shift_date": "2026-06-20", "shift_name": "A", "line": "Line 1"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/operator/shift/" in r.headers["location"]
    assert r.headers["location"].endswith("/entry")
    # the shift now exists in the DB
    db = SessionLocal()
    shifts = db.query(Shift).all()
    assert len(shifts) == 1
    assert shifts[0].status == ShiftStatus.OPEN
    assert shifts[0].line == "Line 1"
    db.close()


def test_resume_does_not_duplicate():
    # open the same shift twice -> only one record
    for _ in range(2):
        client.post(
            "/operator/shift/new",
            data={"shift_date": "2026-06-20", "shift_name": "A"},
            follow_redirects=False,
        )
    db = SessionLocal()
    assert db.query(Shift).count() == 1
    db.close()


def test_different_shift_name_creates_separate():
    client.post(
        "/operator/shift/new",
        data={"shift_date": "2026-06-20", "shift_name": "A"},
        follow_redirects=False,
    )
    client.post(
        "/operator/shift/new",
        data={"shift_date": "2026-06-20", "shift_name": "B"},
        follow_redirects=False,
    )
    db = SessionLocal()
    assert db.query(Shift).count() == 2
    db.close()


def test_redirect_lands_on_working_entry_form():
    r = client.post("/operator/shift/new", data={"shift_date": "2026-06-20", "shift_name": "A"})
    # follow_redirects defaults True -> we should end on the entry form
    assert r.status_code == 200
    assert "Downtime / Loss Event Entry" in r.text


def test_list_shifts_shows_opened():
    client.post(
        "/operator/shift/new",
        data={"shift_date": "2026-06-20", "shift_name": "A"},
        follow_redirects=False,
    )
    r = client.get("/operator/shifts")
    assert r.status_code == 200
    assert "My Shifts" in r.text
    assert "2026-06-20" in r.text
