"""Long-downtime anomaly rule.

Flags any individual downtime event longer than a configurable threshold.
"""

from typing import Any

from app.config import get_settings
from app.services.anomaly.base import Anomaly, AnomalyRule


class LongDowntimeRule(AnomalyRule):
    """Flags downtime events exceeding the configured threshold."""

    name = "long_downtime"

    def __init__(self, threshold_minutes: int | None = None) -> None:
        if threshold_minutes is None:
            threshold_minutes = get_settings().anomaly_downtime_minutes_threshold
        self.threshold_minutes = threshold_minutes

    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        for event in shift_context.get("downtime_events", []):
            duration_min = getattr(event, "duration_minutes", 0)
            if duration_min > self.threshold_minutes:
                severity = "critical" if duration_min > 60 else "warning"
                anomalies.append(
                    Anomaly(
                        rule_name=self.name,
                        severity=severity,
                        message=(
                            f"Downtime of {duration_min:.0f} min exceeds "
                            f"{self.threshold_minutes} min threshold"
                        ),
                        entity_type="downtime",
                        entity_id=getattr(event, "id", None),
                    )
                )
        return anomalies
