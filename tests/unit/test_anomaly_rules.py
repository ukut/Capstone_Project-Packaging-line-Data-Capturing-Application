"""Unit tests for the anomaly detection Strategy pattern.

Each rule is tested in isolation with fabricated shift contexts —
no DB needed, demonstrating one benefit of the Strategy pattern.
"""

from dataclasses import dataclass

from app.services.anomaly.high_reject_rate import HighRejectRateRule
from app.services.anomaly.long_downtime import LongDowntimeRule


@dataclass
class FakeDowntime:
    id: int
    duration_minutes: float


@dataclass
class FakeProduction:
    good_count: int
    reject_count: int


# ---------- LongDowntimeRule ----------


def test_long_downtime_rule_fires_above_threshold():
    rule = LongDowntimeRule(threshold_minutes=30)
    context = {"downtime_events": [FakeDowntime(id=1, duration_minutes=45)]}

    anomalies = rule.evaluate(context)

    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "long_downtime"
    assert anomalies[0].severity == "warning"
    assert anomalies[0].entity_id == 1


def test_long_downtime_rule_critical_above_60():
    rule = LongDowntimeRule(threshold_minutes=30)
    context = {"downtime_events": [FakeDowntime(id=2, duration_minutes=75)]}

    anomalies = rule.evaluate(context)

    assert len(anomalies) == 1
    assert anomalies[0].severity == "critical"


def test_long_downtime_rule_silent_below_threshold():
    rule = LongDowntimeRule(threshold_minutes=30)
    context = {"downtime_events": [FakeDowntime(id=3, duration_minutes=15)]}

    anomalies = rule.evaluate(context)

    assert anomalies == []


def test_long_downtime_rule_handles_empty_context():
    rule = LongDowntimeRule(threshold_minutes=30)
    assert rule.evaluate({}) == []
    assert rule.evaluate({"downtime_events": []}) == []


# ---------- HighRejectRateRule ----------


def test_reject_rate_rule_fires_above_threshold():
    rule = HighRejectRateRule(threshold_percent=2.0)
    context = {
        "production_entries": [
            FakeProduction(good_count=970, reject_count=30),  # 3%
        ],
        "shift": type("S", (), {"id": 99})(),
    }

    anomalies = rule.evaluate(context)

    assert len(anomalies) == 1
    assert anomalies[0].rule_name == "high_reject_rate"
    assert anomalies[0].entity_id == 99


def test_reject_rate_rule_critical_at_2x_threshold():
    rule = HighRejectRateRule(threshold_percent=2.0)
    context = {
        "production_entries": [FakeProduction(good_count=900, reject_count=100)],  # 10%
        "shift": type("S", (), {"id": 1})(),
    }

    anomalies = rule.evaluate(context)
    assert anomalies[0].severity == "critical"


def test_reject_rate_rule_silent_when_no_production():
    rule = HighRejectRateRule(threshold_percent=2.0)
    assert rule.evaluate({"production_entries": []}) == []


def test_reject_rate_rule_silent_below_threshold():
    rule = HighRejectRateRule(threshold_percent=2.0)
    context = {
        "production_entries": [FakeProduction(good_count=995, reject_count=5)],  # 0.5%
    }
    assert rule.evaluate(context) == []
