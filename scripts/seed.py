"""Seed the database with reference data and demo records.

Idempotent: safe to run on every deploy. For each row it checks existence by
the natural key (code/username/name) and inserts only if missing. Running it
twice never duplicates.

What it seeds:
  - SKUs, Machines, BCS categories (locked), Loss types (with suggested BCS)
  - Demo users: admin / operator1 / super1 (bcrypt-hashed passwords)
  - One demo OPEN shift for operator1, so the live URL shows a usable form

Run:
    python -m scripts.seed
"""

from datetime import date

import bcrypt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import loss_event  # noqa: F401  (registers LossEvent for relationships)
from app.models.lookup import SKU, BCSCategory, LossType, Machine
from app.models.shift import Role, Shift, ShiftName, ShiftStatus, User
from scripts.seed_data import (
    BCS_CATEGORIES,
    LOSS_TYPES,
    MACHINES,
    SKUS,
    USERS,
)


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _get_by(db: Session, model, **kw):
    stmt = select(model).filter_by(**kw)
    return db.execute(stmt).scalars().first()


def seed_lookups(db: Session) -> None:
    for row in SKUS:
        if not _get_by(db, SKU, code=row["code"]):
            db.add(SKU(code=row["code"], description=row.get("description")))

    for row in MACHINES:
        if not _get_by(db, Machine, name=row["name"]):
            db.add(Machine(name=row["name"]))

    for row in BCS_CATEGORIES:
        if not _get_by(db, BCSCategory, code=row["code"]):
            db.add(
                BCSCategory(
                    code=row["code"],
                    description=row.get("description"),
                    is_locked=row.get("is_locked", True),
                )
            )

    for row in LOSS_TYPES:
        if not _get_by(db, LossType, code=row["code"]):
            db.add(
                LossType(
                    code=row["code"],
                    description=row.get("description"),
                    suggested_bcs_code=row.get("suggested_bcs_code"),
                )
            )
    db.flush()


def seed_users(db: Session) -> None:
    for row in USERS:
        if not _get_by(db, User, username=row["username"]):
            db.add(
                User(
                    username=row["username"],
                    password_hash=_hash(row["password"]),
                    role=Role(row["role"]),
                )
            )
    db.flush()


def seed_demo_shift(db: Session) -> None:
    """One OPEN shift for operator1 so the live form is immediately usable."""
    operator = _get_by(db, User, username="operator1")
    if operator is None:
        return
    existing = (
        db.execute(
            select(Shift).where(Shift.operator_id == operator.id, Shift.status == ShiftStatus.OPEN)
        )
        .scalars()
        .first()
    )
    if existing is None:
        db.add(
            Shift(
                shift_date=date.today(),
                shift_name=ShiftName.A,
                line="Line 1",
                operator_id=operator.id,
                status=ShiftStatus.OPEN,
            )
        )
    db.flush()


def main() -> None:
    db = SessionLocal()
    try:
        seed_lookups(db)
        seed_users(db)
        seed_demo_shift(db)
        db.commit()
        # Report counts.
        n_sku = len(db.execute(select(SKU)).scalars().all())
        n_mac = len(db.execute(select(Machine)).scalars().all())
        n_bcs = len(db.execute(select(BCSCategory)).scalars().all())
        n_lt = len(db.execute(select(LossType)).scalars().all())
        n_user = len(db.execute(select(User)).scalars().all())
        n_shift = len(db.execute(select(Shift)).scalars().all())
        print(
            f"Seed complete: {n_sku} SKUs, {n_mac} machines, {n_bcs} BCS, "
            f"{n_lt} loss types, {n_user} users, {n_shift} shift(s)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
