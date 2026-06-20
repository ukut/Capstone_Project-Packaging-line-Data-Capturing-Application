"""Anomaly detection rules — Strategy pattern (revised for downtime tracking).

The original scaffold had a reject-rate rule, which no longer applies now that
the app tracks downtime/loss events rather than production counts. These three
rules replace it, each operating on a shift's collection of LossEvents:

    LongBreakdownRule        — any single event longer than a threshold
    HighTotalDowntimeRule    — total downtime in a shift exceeds a threshold
    RepeatedMachineFailureRule — same machine fails N+ times in one shift

The Strategy pattern is unchanged: each rule is a class implementing
evaluate(), registered in ALL_RULES, and the review service iterates them.
Adding a rule = one new class + one registry line (Open/Closed Principle).
"""

from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Anomaly:
    rule_name: str
    severity: str  # "info" | "warning" | "critical"
    message: str
    entity_type: str
    entity_id: int | None = None


class AnomalyRule(ABC):
    name: str

    @abstractmethod
    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        """Return any anomalies for the shift. shift_context has keys:
        'shift' and 'loss_events' (each event exposing .duration_minutes,
        .machine_id, .id)."""
        ...


class LongBreakdownRule(AnomalyRule):
    """Flag any single loss event longer than threshold_minutes."""

    name = "long_breakdown"

    def __init__(self, threshold_minutes: int = 30) -> None:
        self.threshold_minutes = threshold_minutes

    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        out: list[Anomaly] = []
        for ev in shift_context.get("loss_events", []):
            dur = getattr(ev, "duration_minutes", 0)
            if dur > self.threshold_minutes:
                out.append(
                    Anomaly(
                        rule_name=self.name,
                        severity="critical" if dur > 60 else "warning",
                        message=f"Single event of {dur} min exceeds {self.threshold_minutes} min",
                        entity_type="loss_event",
                        entity_id=getattr(ev, "id", None),
                    )
                )
        return out


class HighTotalDowntimeRule(AnomalyRule):
    """Flag a shift whose total downtime exceeds threshold_minutes."""

    name = "high_total_downtime"

    def __init__(self, threshold_minutes: int = 120) -> None:
        self.threshold_minutes = threshold_minutes

    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        events = shift_context.get("loss_events", [])
        total = sum(getattr(e, "duration_minutes", 0) for e in events)
        if total <= self.threshold_minutes:
            return []
        return [
            Anomaly(
                rule_name=self.name,
                severity="critical" if total > self.threshold_minutes * 2 else "warning",
                message=f"Total shift downtime {total} min exceeds {self.threshold_minutes} min",
                entity_type="shift",
                entity_id=getattr(shift_context.get("shift"), "id", None),
            )
        ]


class RepeatedMachineFailureRule(AnomalyRule):
    """Flag a machine that fails repeat_threshold+ times within the shift."""

    name = "repeated_machine_failure"

    def __init__(self, repeat_threshold: int = 3) -> None:
        self.repeat_threshold = repeat_threshold

    def evaluate(self, shift_context: dict[str, Any]) -> list[Anomaly]:
        events = shift_context.get("loss_events", [])
        counts = Counter(getattr(e, "machine_id", None) for e in events)
        out: list[Anomaly] = []
        for machine_id, n in counts.items():
            if machine_id is not None and n >= self.repeat_threshold:
                out.append(
                    Anomaly(
                        rule_name=self.name,
                        severity="warning",
                        message=f"Machine {machine_id} failed {n} times this shift",
                        entity_type="machine",
                        entity_id=machine_id,
                    )
                )
        return out


ALL_RULES: list[AnomalyRule] = [
    LongBreakdownRule(),
    HighTotalDowntimeRule(),
    RepeatedMachineFailureRule(),
]
