"""User and Shift models.

User: authentication + role-based access (operator / supervisor / admin).
Shift: groups loss events for a working period so the supervisor can review,
approve, and lock a whole shift's data at once.
"""
import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(str, enum.Enum):
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ShiftName(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    DAY = "day"
    NIGHT = "night"


class ShiftStatus(str, enum.Enum):
    OPEN = "open"               # operator is still entering events
    PENDING_REVIEW = "pending"  # operator closed it; awaiting supervisor
    APPROVED = "approved"       # supervisor approved (read-only)
    LOCKED = "locked"           # locked; edits require admin override


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.OPERATOR)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Shift(Base):
    """A working shift that groups loss events for review/approval."""

    __tablename__ = "shift"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_name: Mapped[ShiftName] = mapped_column(Enum(ShiftName), nullable=False)
    line: Mapped[str | None] = mapped_column(String(64), nullable=True)

    operator_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    supervisor_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)

    status: Mapped[ShiftStatus] = mapped_column(
        Enum(ShiftStatus), default=ShiftStatus.OPEN, nullable=False
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    operator: Mapped["User"] = relationship(foreign_keys=[operator_id])
    supervisor: Mapped["User | None"] = relationship(foreign_keys=[supervisor_id])
    loss_events: Mapped[list["LossEvent"]] = relationship(  # noqa: F821
        back_populates="shift", cascade="all, delete-orphan"
    )
