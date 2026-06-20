"""Unit tests for derived fields and anomaly rules.

The derived-field tests use the ACTUAL values from the historical Excel sheet
(1-Apr-2020 rows) as fixtures — so these tests prove the new system reproduces
the legacy calculated columns exactly. This is cited in docs/DESIGN.md as
evidence of faithful migration.
"""
from datetime import date, time

import pytest

from app.services.anomaly.rules import (
    HighTotalDowntimeRule,
    LongBreakdownRule,
    RepeatedMachineFailureRule,
)
from app.services.derived import compute_duration_minutes, derive_fields


# ---------- Derived fields: tested against real historical data ----------

@pytest.mark.parametrize(
    "start,stop,exp_min,exp_hhmm,exp_hr",
    [
        (time(7, 0), time(8, 0), 60, "1:00", 1.00),
        (time(8, 0), time(8, 48), 48, "0:48", 0.80),
        (time(9, 0), time(9, 7), 7, "0:07", 0.12),
        (time(10, 0), time(10, 12), 12, "0:12", 0.20),
        (time(11, 0), time(11, 17), 17, "0:17", 0.28),
    ],
)
def test_duration_matches_legacy_excel(start, stop, exp_min, exp_hhmm, exp_hr):
    d = date(2020, 4, 1)
    fields = derive_fields(d, start, stop)
    assert fields.duration_minutes == exp_min
    assert fields.duration_hhmm == exp_hhmm
    assert fields.duration_hours == exp_hr


def test_date_derived_fields_match_legacy():
    fields = derive_fields(date(2020, 4, 1), time(7, 0), time(8, 0))
    assert fields.week == 14
    assert fields.year == 2020
    assert fields.month == 4
    assert fields.week_year == "Wk14-2020"
    assert fields.month_year == "M4-2020"


def test_overnight_event_rolls_over_midnight():
    # 23:40 -> 00:15 should be 35 minutes, not negative
    minutes = compute_duration_minutes(date(2020, 4, 1), time(23, 40), time(0, 15))
    assert minutes == 35


# ---------- Anomaly rules ----------

class FakeEvent:
    def __init__(self, id, duration_minutes, machine_id):
        self.id = id
        self.duration_minutes = duration_minutes
        self.machine_id = machine_id


def test_long_breakdown_fires_above_threshold():
    rule = LongBreakdownRule(threshold_minutes=30)
    ctx = {"loss_events": [FakeEvent(1, 45, 2)]}
    anomalies = rule.evaluate(ctx)
    assert len(anomalies) == 1
    assert anomalies[0].severity == "warning"


def test_long_breakdown_critical_above_60():
    rule = LongBreakdownRule(threshold_minutes=30)
    ctx = {"loss_events": [FakeEvent(1, 75, 2)]}
    assert rule.evaluate(ctx)[0].severity == "critical"


def test_long_breakdown_silent_below_threshold():
    rule = LongBreakdownRule(threshold_minutes=30)
    ctx = {"loss_events": [FakeEvent(1, 15, 2)]}
    assert rule.evaluate(ctx) == []


def test_high_total_downtime_fires():
    rule = HighTotalDowntimeRule(threshold_minutes=120)
    ctx = {
        "loss_events": [FakeEvent(1, 80, 1), FakeEvent(2, 70, 2)],  # 150 total
        "shift": type("S", (), {"id": 9})(),
    }
    anomalies = rule.evaluate(ctx)
    assert len(anomalies) == 1
    assert anomalies[0].entity_id == 9


def test_high_total_downtime_silent_below():
    rule = HighTotalDowntimeRule(threshold_minutes=120)
    ctx = {"loss_events": [FakeEvent(1, 30, 1)], "shift": type("S", (), {"id": 9})()}
    assert rule.evaluate(ctx) == []


def test_repeated_machine_failure_fires():
    rule = RepeatedMachineFailureRule(repeat_threshold=3)
    ctx = {"loss_events": [FakeEvent(i, 10, 5) for i in range(3)]}  # machine 5 x3
    anomalies = rule.evaluate(ctx)
    assert len(anomalies) == 1
    assert anomalies[0].entity_id == 5


def test_repeated_machine_failure_silent_below():
    rule = RepeatedMachineFailureRule(repeat_threshold=3)
    ctx = {"loss_events": [FakeEvent(1, 10, 5), FakeEvent(2, 10, 5)]}  # only x2
    assert rule.evaluate(ctx) == []
