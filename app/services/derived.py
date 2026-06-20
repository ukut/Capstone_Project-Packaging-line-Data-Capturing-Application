"""Derived-field computation.

The legacy Excel sheet stored eight columns that were either typed by hand
(error-prone) or kept as fragile spreadsheet formulas:

    Duration (h:mm), Duration (min), Duration (hr),
    Month, Week, Year, Week-Year, Month-Year

This module computes all of them deterministically from the three values the
operator actually enters: event_date, event_start, event_stop. Computing them
in one place means the legacy Excel export and the on-screen display can never
disagree, and an operator can never enter "90 min" in one column but "1.0 hr"
in another.

Overnight events: if event_stop is earlier than event_start (e.g. a breakdown
spanning midnight, 23:40 -> 00:15), the stop is treated as the next day.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class DerivedFields:
    """All values derived from (event_date, event_start, event_stop)."""

    duration_hhmm: str  # "1:00"  — legacy "Duration"
    duration_minutes: int  # 60      — legacy "Duration (min)"
    duration_hours: float  # 1.00    — legacy "Duration (hr)"
    month: int  # 4       — legacy "Month"
    week: int  # 14      — legacy "Week" (ISO week)
    year: int  # 2020    — legacy "Year"
    week_year: str  # "Wk14-2020"  — legacy "Week-Year"
    month_year: str  # "M4-2020"    — legacy "Month-Year"


def compute_duration_minutes(event_date: date, start: time, stop: time) -> int:
    """Whole minutes between start and stop, handling midnight rollover."""
    start_dt = datetime.combine(event_date, start)
    stop_dt = datetime.combine(event_date, stop)
    if stop_dt < start_dt:
        # Event ran past midnight; stop belongs to the next day.
        stop_dt += timedelta(days=1)
    delta = stop_dt - start_dt
    return int(delta.total_seconds() // 60)


def derive_fields(event_date: date, start: time, stop: time) -> DerivedFields:
    """Compute every legacy derived column from the three entered values."""
    total_minutes = compute_duration_minutes(event_date, start, stop)

    hours, minutes = divmod(total_minutes, 60)
    duration_hhmm = f"{hours}:{minutes:02d}"
    duration_hours = round(total_minutes / 60, 2)

    iso_year, iso_week, _ = event_date.isocalendar()

    return DerivedFields(
        duration_hhmm=duration_hhmm,
        duration_minutes=total_minutes,
        duration_hours=duration_hours,
        month=event_date.month,
        week=iso_week,
        year=event_date.year,
        week_year=f"Wk{iso_week}-{event_date.year}",
        month_year=f"M{event_date.month}-{event_date.year}",
    )
