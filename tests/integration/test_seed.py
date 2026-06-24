"""Tests for the seed script — idempotency and content."""

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.shift import Shift, ShiftStatus, User
from scripts.seed import seed_demo_shift, seed_lookups, seed_users


def _fresh():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_seed_populates_all_lookups():
    _fresh()
    db = SessionLocal()
    seed_lookups(db)
    db.commit()
    assert len(db.execute(select(SKU)).scalars().all()) == 5
    assert len(db.execute(select(Machine)).scalars().all()) == 7
    assert len(db.execute(select(BCSCategory)).scalars().all()) == 5
    assert len(db.execute(select(LossType)).scalars().all()) == 7
    db.close()


def test_bcs_categories_are_locked():
    _fresh()
    db = SessionLocal()
    seed_lookups(db)
    db.commit()
    cats = db.execute(select(BCSCategory)).scalars().all()
    assert all(c.is_locked for c in cats)
    db.close()


def test_loss_types_have_suggested_bcs():
    _fresh()
    db = SessionLocal()
    seed_lookups(db)
    db.commit()
    cilt = db.execute(select(LossType).where(LossType.code == "CILT")).scalars().first()
    assert cilt.suggested_bcs_code == "PlannedDownTime"
    db.close()


def test_seed_users_hashes_passwords():
    _fresh()
    db = SessionLocal()
    seed_users(db)
    db.commit()
    admin = db.execute(select(User).where(User.username == "admin")).scalars().first()
    assert admin is not None
    assert admin.password_hash != "admin"  # not plaintext
    assert admin.password_hash.startswith("$2b$")  # bcrypt format
    db.close()


def test_seed_is_idempotent():
    _fresh()
    db = SessionLocal()
    seed_lookups(db)
    seed_users(db)
    seed_demo_shift(db)
    db.commit()
    seed_lookups(db)
    seed_users(db)
    seed_demo_shift(db)
    db.commit()
    assert len(db.execute(select(SKU)).scalars().all()) == 5
    assert len(db.execute(select(User)).scalars().all()) == 3
    assert len(db.execute(select(Shift)).scalars().all()) == 1
    db.close()


def test_demo_shift_is_open():
    _fresh()
    db = SessionLocal()
    seed_users(db)
    seed_demo_shift(db)
    db.commit()
    shift = db.execute(select(Shift)).scalars().first()
    assert shift.status == ShiftStatus.OPEN
    db.close()
