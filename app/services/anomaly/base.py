"""Anomaly detection rules — Strategy pattern.

WHY this pattern (for the design document):
- Each rule is a self-contained class with a uniform interface.
- Adding a new rule means creating one new class — no edits to existing code (OCP).
- Rules are configured/composed at runtime, not hard-coded in supervisor screens.
- Each rule is independently unit-testable.

The supervisor review service iterates over a registered list of rules and
collects every Anomaly produced. Rules never mutate data — they only report.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Anomaly:
    """A single anomaly reported by a rule against a shift's data."""

    rule_name: str
    severity: str  # "info" | "warning" | "critical"
    message: str
    entity_type: str  # e.g. "downtime", "production"
    entity_id: int | None = None


class AnomalyRule(ABC):
    """Abstract base for anomaly detection rules.

    Subclasses implement `evaluate()` which returns zero or more Anomaly objects
    for the given shift context.
    """

    name: str

    @abstractmethod
    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        """Inspect shift data and return any anomalies found.

        Args:
            shift_context: dict containing 'shift', 'production_entries',
                'downtime_events', 'quality_checks', 'material_usage'.

        Returns:
            List of Anomaly objects. Empty list = no anomalies.
        """
        ...
