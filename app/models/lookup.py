"""Lookup (reference) tables — with governance refinements.

Two refinements over the base version:

1. BCSCategory.is_locked — marks the BCS list as a controlled standard.
   BCS exists for cross-brewery comparison; if any brewery could freely add
   categories, the comparison breaks. Locked categories can only be changed by
   an admin (enforced in the admin service, not just convention).

2. LossType.suggested_bcs_code — each operational loss type carries the BCS
   bucket it *usually* maps to. The operator form pre-selects this BCS category
   when a Type of Loss is chosen, but the operator can override it (the real
   data shows Type of Loss and BCS legitimately differ per event). This is
   "guided entry with override": it captures institutional mapping knowledge
   while respecting floor-level judgement.

The two-independent-foreign-keys structure on LossEvent is unchanged — these
refinements only add guidance and governance, not new required relationships.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SKU(Base):
    __tablename__ = "sku"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    loss_events: Mapped[list["LossEvent"]] = relationship(back_populates="sku")  # noqa: F821


class BCSCategory(Base):
    """Brewery Comparison System category — a controlled, group-wide standard.

    is_locked=True means this is one of the official standard categories and may
    only be modified by an admin. The five canonical categories ship locked.
    """

    __tablename__ = "bcs_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    loss_events: Mapped[list["LossEvent"]] = relationship(back_populates="bcs_category")  # noqa: F821


class LossType(Base):
    """Operational loss type — the real-time, floor-level description.

    suggested_bcs_code points at the BCS category this loss type usually maps to.
    It's a *suggestion* the operator form pre-fills, not an enforced constraint.
    Stored as the BCS code (string) rather than an FK to keep seeding simple and
    to tolerate a loss type whose suggested bucket is later retired.
    """

    __tablename__ = "loss_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suggested_bcs_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    loss_events: Mapped[list["LossEvent"]] = relationship(back_populates="loss_type")  # noqa: F821


class Machine(Base):
    __tablename__ = "machine"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    loss_events: Mapped[list["LossEvent"]] = relationship(back_populates="machine")  # noqa: F821
