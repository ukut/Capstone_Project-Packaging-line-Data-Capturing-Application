"""Pydantic schemas for loss-event input validation.

The schema is the FIRST line of data-quality defence — the thing that makes
the new app better than the Excel sheet. Every rule that the spreadsheet
relied on a human to remember is encoded here and enforced before anything
touches the database:

- start/stop must be valid times
- the four foreign keys must be present
- failure descriptions have length limits
- (cross-field) stop != start is checked in the service, where we also
  handle the legitimate overnight case (stop earlier than start = next day)

Validation lives here, not in the route or the template, so the SAME rules
apply whether data arrives from the web form, a future API, or a bulk import.
"""

from datetime import date, time

from pydantic import BaseModel, Field, field_validator


class LossEventCreate(BaseModel):
    """Validated payload for creating one loss event."""

    event_date: date
    event_start: time
    event_stop: time

    sku_id: int = Field(..., gt=0, description="FK to sku")
    machine_id: int = Field(..., gt=0, description="FK to machine")
    loss_type_id: int = Field(..., gt=0, description="FK to loss_type")
    bcs_category_id: int = Field(..., gt=0, description="FK to bcs_category")

    functional_failure_description: str | None = Field(default=None, max_length=500)
    failure_mode_description: str | None = Field(default=None, max_length=500)

    @field_validator("functional_failure_description", "failure_mode_description")
    @classmethod
    def strip_blank_to_none(cls, v: str | None) -> str | None:
        """Treat whitespace-only text as empty, so we never store '   '."""
        if v is None:
            return None
        v = v.strip()
        return v or None
