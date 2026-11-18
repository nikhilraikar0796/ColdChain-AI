
import unittest

from app.rules.engine import ColdChainRuleEngine
from app.rules.models import RuleStatus, Severity


class TestColdChainRuleEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ColdChainRuleEngine()

    # -----------------------------------------
    # CC-001: Tier 2 escalation
    # -----------------------------------------

    def test_tier2_rule_triggers(self):
        record = {
            "telemetry_id": 101,
            "risk_classification": "High Risk",
            "delay_probability": 0.80,
        }

        result = self.engine.evaluate_rule("CC-001", record)

        self.assertEqual(result.status, RuleStatus.TRIGGERED)
        self.assertEqual(result.severity, Severity.HIGH)
        self.assertTrue(result.recommended_action)

    def test_tier2_rule_does_not_trigger_below_threshold(self):
        record = {
            "risk_classification": "High Risk",
            "delay_probability": 0.40,
        }

        result = self.engine.evaluate_rule("CC-001", record)

        self.assertEqual(result.status, RuleStatus.NOT_TRIGGERED)

    def test_tier2_rule_does_not_trigger_at_threshold(self):
        record = {
            "risk_classification": "High Risk",
            "delay_probability": 0.65,
        }

        result = self.engine.evaluate_rule("CC-001", record)

        self.assertEqual(result.status, RuleStatus.NOT_TRIGGERED)

    def test_tier2_rule_does_not_trigger_for_low_risk(self):
        record = {
            "risk_classification": "Low Risk",
            "delay_probability": 0.90,
        }

        result = self.engine.evaluate_rule("CC-001", record)

        self.assertEqual(result.status, RuleStatus.NOT_TRIGGERED)

    def test_tier2_rule_handles_missing_delay(self):
        record = {
            "risk_classification": "High Risk",
        }

        result = self.engine.evaluate_rule("CC-001", record)

        self.assertEqual(result.status, RuleStatus.NOT_EVALUABLE)

    # -----------------------------------------
    # CC-002: Temperature breach
    # -----------------------------------------

    def test_temperature_rule_triggers(self):
        record = {
            "cargo_category": "fresh_perishables",
            "iot_temperature": 5.2,
        }

        result = self.engine.evaluate_rule("CC-002", record)

        self.assertEqual(result.status, RuleStatus.TRIGGERED)
        self.assertEqual(result.severity, Severity.CRITICAL)

    def test_temperature_rule_does_not_trigger_at_threshold(self):
        record = {
            "cargo_category": "fresh_perishables",
            "iot_temperature": 4.0,
        }

        result = self.engine.evaluate_rule("CC-002", record)

        self.assertEqual(result.status, RuleStatus.NOT_TRIGGERED)

    def test_temperature_rule_requires_cargo_category(self):
        record = {
            "iot_temperature": 8.0,
        }

        result = self.engine.evaluate_rule("CC-002", record)

        self.assertEqual(result.status, RuleStatus.NOT_EVALUABLE)

    # -----------------------------------------
    # CC-003: Port congestion diversion
    # -----------------------------------------

    def test_port_rule_triggers(self):
        record = {
            "port_name": "Port of Long Beach",
            "port_congestion_level": 8.5,
        }

        result = self.engine.evaluate_rule("CC-003", record)

        self.assertEqual(result.status, RuleStatus.TRIGGERED)
        self.assertEqual(result.severity, Severity.HIGH)

    def test_port_rule_does_not_trigger_at_threshold(self):
        record = {
            "port_name": "Port of Los Angeles",
            "port_congestion_level": 7.0,
        }

        result = self.engine.evaluate_rule("CC-003", record)

        self.assertEqual(result.status, RuleStatus.NOT_TRIGGERED)

    def test_port_rule_requires_port_identity(self):
        record = {
            "port_congestion_level": 9.0,
        }

        result = self.engine.evaluate_rule("CC-003", record)

        self.assertEqual(result.status, RuleStatus.NOT_EVALUABLE)

    # -----------------------------------------
    # Engine behaviour
    # -----------------------------------------

    def test_evaluate_all_returns_three_results(self):
        record = {
            "telemetry_id": 202,
            "risk_classification": "High Risk",
            "delay_probability": 0.90,
            "iot_temperature": 8.0,
            "port_congestion_level": 9.0,
        }

        results = self.engine.evaluate_all(record)

        self.assertEqual(len(results), 3)

        statuses = {
            result.rule_id: result.status
            for result in results
        }

        self.assertEqual(
            statuses["CC-001"],
            RuleStatus.TRIGGERED,
        )

        self.assertEqual(
            statuses["CC-002"],
            RuleStatus.NOT_EVALUABLE,
        )

        self.assertEqual(
            statuses["CC-003"],
            RuleStatus.NOT_EVALUABLE,
        )


    def test_evaluation_summary_counts_results(self):
        record = {
            "telemetry_id": 303,
            "risk_classification": "High Risk",
            "delay_probability": 0.90,
            "iot_temperature": 8.0,
            "port_congestion_level": 9.0,
        }

        summary = self.engine.evaluate_summary(record)

        self.assertEqual(summary.total_rules, 3)
        self.assertEqual(summary.triggered_count, 1)
        self.assertEqual(summary.not_triggered_count, 0)
        self.assertEqual(summary.not_evaluable_count, 2)

        self.assertEqual(len(summary.triggered_alerts), 1)
        self.assertEqual(len(summary.needs_information), 2)

    def test_evaluation_summary_with_no_triggered_rules(self):
        record = {
            "telemetry_id": 304,
            "risk_classification": "Low Risk",
            "delay_probability": 0.30,
        }

        summary = self.engine.evaluate_summary(record)

        self.assertEqual(summary.total_rules, 3)
        self.assertEqual(summary.triggered_count, 0)
        self.assertEqual(summary.not_triggered_count, 1)
        self.assertEqual(summary.not_evaluable_count, 2)


    def test_unknown_rule_raises_error(self):
        with self.assertRaises(ValueError):
            self.engine.evaluate_rule("CC-999", {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
