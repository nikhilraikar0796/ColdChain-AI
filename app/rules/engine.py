
from typing import Any

from app.rules.models import (
    RuleResult,
    RuleStatus,
    RuleEvaluationSummary,
)
from app.rules.conditions import (
    evaluate_equals,
    evaluate_greater_than,
    combine_and,
)
from app.rules.registry import get_all_rules


class ColdChainRuleEngine:
    """Evaluate registered cold-chain operational rules."""

    def evaluate_rule(
        self,
        rule_id: str,
        record: dict[str, Any],
    ) -> RuleResult:

        rules = {
            rule.rule_id: rule
            for rule in get_all_rules()
        }

        if rule_id not in rules:
            raise ValueError(f"Unknown rule ID: {rule_id}")

        rule = rules[rule_id]

        evaluators = {
            "CC-001": self._evaluate_tier2_escalation,
            "CC-002": self._evaluate_temperature_breach,
            "CC-003": self._evaluate_port_diversion,
        }

        if rule_id not in evaluators:
            raise ValueError(f"No evaluator implemented for {rule_id}")

        return evaluators[rule_id](record, rule)

    def evaluate_all(
        self,
        record: dict[str, Any],
    ) -> list[RuleResult]:

        return [
            self.evaluate_rule(rule.rule_id, record)
            for rule in get_all_rules()
        ]

    def evaluate_summary(
        self,
        record: dict[str, Any],
    ) -> RuleEvaluationSummary:
        """Evaluate all rules and produce an operational summary."""

        results = self.evaluate_all(record)

        triggered = sum(
            r.status == RuleStatus.TRIGGERED for r in results
        )

        not_triggered = sum(
            r.status == RuleStatus.NOT_TRIGGERED for r in results
        )

        not_evaluable = sum(
            r.status == RuleStatus.NOT_EVALUABLE for r in results
        )

        return RuleEvaluationSummary(
            record_id=record.get("telemetry_id"),
            total_rules=len(results),
            triggered_count=triggered,
            not_triggered_count=not_triggered,
            not_evaluable_count=not_evaluable,
            results=results,
        )

    @staticmethod
    def _base_result(
        rule: Any,
        status: RuleStatus,
        message: str,
        record: dict[str, Any],
        evidence: dict[str, Any] | None = None,
        recommended_action: str = "",
    ) -> RuleResult:

        return RuleResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            status=status,
            severity=(
                rule.severity
                if status == RuleStatus.TRIGGERED
                else None
            ),
            message=message,
            recommended_action=recommended_action,
            record_id=record.get("telemetry_id"),
            evidence=evidence or {},
            limitations=(
                [rule.applicability_note]
                if rule.applicability_note
                else []
            ),
        )

    def _evaluate_tier2_escalation(
        self,
        record: dict[str, Any],
        rule: Any,
    ) -> RuleResult:

        risk_status, risk_message = evaluate_equals(
            record,
            "risk_classification",
            "High Risk",
        )

        delay_status, delay_message = evaluate_greater_than(
            record,
            "delay_probability",
            0.65,
        )

        status = combine_and(risk_status, delay_status)

        action = (
            "Escalation candidate: refer to Tier 2 Logistics Manager."
            if status == RuleStatus.TRIGGERED
            else ""
        )

        return self._base_result(
            rule,
            status,
            f"{risk_message} {delay_message}",
            record,
            {
                "risk_classification": record.get("risk_classification"),
                "delay_probability": record.get("delay_probability"),
                "threshold": 0.65,
            },
            action,
        )

    def _evaluate_temperature_breach(
        self,
        record: dict[str, Any],
        rule: Any,
    ) -> RuleResult:

        cargo_status, cargo_message = evaluate_equals(
            record,
            "cargo_category",
            "fresh_perishables",
        )

        temperature_status, temperature_message = evaluate_greater_than(
            record,
            "iot_temperature",
            4.0,
        )

        status = combine_and(cargo_status, temperature_status)

        action = (
            "Contact the driver and verify auxiliary cooling. "
            "Consider emergency cold-storage diversion only after "
            "confirming an ETA delay greater than one hour."
            if status == RuleStatus.TRIGGERED
            else ""
        )

        return self._base_result(
            rule,
            status,
            f"{cargo_message} {temperature_message}",
            record,
            {
                "cargo_category": record.get("cargo_category"),
                "iot_temperature": record.get("iot_temperature"),
                "threshold_celsius": 4.0,
            },
            action,
        )

    def _evaluate_port_diversion(
        self,
        record: dict[str, Any],
        rule: Any,
    ) -> RuleResult:

        port_name = record.get("port_name")

        supported_ports = {
            "port of los angeles",
            "port of long beach",
            "los angeles",
            "long beach",
        }

        if port_name is None or not str(port_name).strip():
            port_status = RuleStatus.NOT_EVALUABLE
            port_message = "Port identity is missing."

        elif str(port_name).strip().casefold() in supported_ports:
            port_status = RuleStatus.TRIGGERED
            port_message = "Port matches LA/Long Beach."

        else:
            port_status = RuleStatus.NOT_TRIGGERED
            port_message = "Port is not LA/Long Beach."

        congestion_status, congestion_message = evaluate_greater_than(
            record,
            "port_congestion_level",
            7.0,
        )

        status = combine_and(port_status, congestion_status)

        action = (
            "Suspend the standard route and consider diversion "
            "to the Inland Empire Overflow Depot, San Bernardino."
            if status == RuleStatus.TRIGGERED
            else ""
        )

        return self._base_result(
            rule,
            status,
            f"{port_message} {congestion_message}",
            record,
            {
                "port_name": port_name,
                "port_congestion_level": record.get(
                    "port_congestion_level"
                ),
                "threshold": 7.0,
            },
            action,
        )
