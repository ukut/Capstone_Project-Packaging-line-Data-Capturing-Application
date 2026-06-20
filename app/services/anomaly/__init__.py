"""Anomaly detection — Strategy pattern (downtime rules)."""

from app.services.anomaly.rules import (
    ALL_RULES,
    Anomaly,
    AnomalyRule,
    HighTotalDowntimeRule,
    LongBreakdownRule,
    RepeatedMachineFailureRule,
)

__all__ = [
    "ALL_RULES",
    "Anomaly",
    "AnomalyRule",
    "HighTotalDowntimeRule",
    "LongBreakdownRule",
    "RepeatedMachineFailureRule",
]
