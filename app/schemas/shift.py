"""Pydantic schema for opening a shift."""

from datetime import date

from pydantic import BaseModel, Field

from app.models.shift import ShiftName


class ShiftCreate(BaseModel):
    """Validated payload for opening a new shift."""

    shift_date: date
    shift_name: ShiftName
    line: str | None = Field(default=None, max_length=64)
