
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RuleStatus(str, Enum):
    TRIGGERED = "triggered"
    NOT_TRIGGERED = "not_triggered"
    NOT_EVALUABLE = "not_evaluable"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class RuleDefinition:
    """Metadata describing an operational business rule."""

    rule_id: str
    name: str
    description: str
    severity: Severity
    required_fields: tuple[str, ...]
    applicability_note: str = ""


@dataclass
class RuleResult:
    """Result produced when an operational rule is evaluated."""

    rule_id: str
    rule_name: str
    status: RuleStatus

    severity: Severity | None = None
    message: str = ""
    recommended_action: str = ""

    record_id: int | str | None = None

    evidence: dict[str, Any] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)


@dataclass
class RuleEvaluationSummary:
    """Summary of all rule evaluations for one record."""

    record_id: int | str | None
    total_rules: int
    triggered_count: int
    not_triggered_count: int
    not_evaluable_count: int
    results: list[RuleResult]

    @property
    def triggered_alerts(self) -> list[RuleResult]:
        return [
            result for result in self.results
            if result.status == RuleStatus.TRIGGERED
        ]

    @property
    def needs_information(self) -> list[RuleResult]:
        return [
            result for result in self.results
            if result.status == RuleStatus.NOT_EVALUABLE
        ]
