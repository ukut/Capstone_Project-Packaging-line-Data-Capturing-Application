"""High-reject-rate anomaly rule.

Flags shifts where overall reject rate exceeds the configured threshold.
"""

from typing import Any

from app.config import get_settings
from app.services.anomaly.base import Anomaly, AnomalyRule


class HighRejectRateRule(AnomalyRule):
    """Flags a shift where total reject rate (rejects / (good + rejects)) is above threshold."""

    name = "high_reject_rate"

    def __init__(self, threshold_percent: float | None = None) -> None:
        if threshold_percent is None:
            threshold_percent = get_settings().anomaly_reject_rate_percent_threshold
        self.threshold_percent = threshold_percent

    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        entries = shift_context.get("production_entries", [])
        total_good = sum(getattr(e, "good_count", 0) for e in entries)
        total_reject = sum(getattr(e, "reject_count", 0) for e in entries)
        total = total_good + total_reject

        if total == 0:
            return []

        reject_rate = (total_reject / total) * 100
        if reject_rate <= self.threshold_percent:
            return []

        severity = "critical" if reject_rate > self.threshold_percent * 2 else "warning"
        return [
            Anomaly(
                rule_name=self.name,
                severity=severity,
                message=(
                    f"Shift reject rate {reject_rate:.2f}% exceeds "
                    f"{self.threshold_percent:.2f}% threshold "
                    f"({total_reject} of {total} units)"
                ),
                entity_type="shift",
                entity_id=getattr(shift_context.get("shift"), "id", None),
            )
        ]
