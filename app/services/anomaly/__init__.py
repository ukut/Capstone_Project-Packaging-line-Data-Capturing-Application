"""Anomaly detection — Strategy pattern.

Public API:
    Anomaly        — value object describing a detected anomaly
    AnomalyRule    — abstract base for rules
    ALL_RULES      — default registered rules; supervisor service iterates this list

Adding a new rule:
    1. Create a new file `<rule_name>.py` with a class inheriting AnomalyRule
    2. Add it to ALL_RULES below
    3. Add a unit test in tests/unit/test_anomaly_rules.py
"""

from app.services.anomaly.base import Anomaly, AnomalyRule
from app.services.anomaly.high_reject_rate import HighRejectRateRule
from app.services.anomaly.long_downtime import LongDowntimeRule

ALL_RULES: list[AnomalyRule] = [
    LongDowntimeRule(),
    HighRejectRateRule(),
]

__all__ = ["Anomaly", "AnomalyRule", "ALL_RULES"]
