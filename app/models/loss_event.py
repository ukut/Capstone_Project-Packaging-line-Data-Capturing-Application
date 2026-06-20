"""LossEvent — the core table.

One row per downtime / loss event, mirroring the legacy Excel sheet but
storing ONLY the values an operator actually types:
    - date
    - event_start (clock time)
    - event_stop (clock time)
    - sku, bcs_category, loss_type, machine  (foreign keys to lookups)
    - functional_failure_description (free text)
    - failure_mode_description (free text)

Everything the legacy sheet stored as a separate manually-typed-or-formula
column is DERIVED at read time from (date, event_start, event_stop):
    duration (h:mm), duration_minutes, duration_hours,
    month, week, year, week_year, month_year

This is the central design improvement over the workbook: each fact is
captured once and derived representations are computed deterministically,
eliminating the inconsistency that manual multi-column entry allowed.
See app/services/derived.py for the derivation logic.
"""
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LossEvent(Base):
    __tablename__ = "loss_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- grouping ---
    shift_id: Mapped[int] = mapped_column(ForeignKey("shift.id"), nullable=False)

    # --- values the operator types ---
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_start: Mapped[time] = mapped_column(Time, nullable=False)
    event_stop: Mapped[time] = mapped_column(Time, nullable=False)

    sku_id: Mapped[int] = mapped_column(ForeignKey("sku.id"), nullable=False)
    bcs_category_id: Mapped[int] = mapped_column(ForeignKey("bcs_category.id"), nullable=False)
    loss_type_id: Mapped[int] = mapped_column(ForeignKey("loss_type.id"), nullable=False)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machine.id"), nullable=False)

    functional_failure_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    failure_mode_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- audit ---
    created_by_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # --- relationships ---
    shift: Mapped["Shift"] = relationship(back_populates="loss_events")  # noqa: F821
    sku: Mapped["SKU"] = relationship(back_populates="loss_events")  # noqa: F821
    bcs_category: Mapped["BCSCategory"] = relationship(back_populates="loss_events")  # noqa: F821
    loss_type: Mapped["LossType"] = relationship(back_populates="loss_events")  # noqa: F821
    machine: Mapped["Machine"] = relationship(back_populates="loss_events")  # noqa: F821
    created_by: Mapped["User"] = relationship()  # noqa: F821
