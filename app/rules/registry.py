
from app.rules.models import RuleDefinition, Severity


# Central catalogue of ColdChain-AI operational rules.
RULE_REGISTRY: dict[str, RuleDefinition] = {

    "CC-001": RuleDefinition(
        rule_id="CC-001",
        name="Tier 2 Logistics Escalation",
        description=(
            "Identify High Risk records where delay probability "
            "exceeds 0.65."
        ),
        severity=Severity.HIGH,
        required_fields=(
            "risk_classification",
            "delay_probability",
        ),
        applicability_note=(
            "Identifies escalation candidates. Actual escalation "
            "status is not available in the dataset."
        ),
    ),

    "CC-002": RuleDefinition(
        rule_id="CC-002",
        name="Fresh Perishable Temperature Breach",
        description=(
            "Identify fresh-perishable cargo with temperatures "
            "above 4 degrees Celsius."
        ),
        severity=Severity.CRITICAL,
        required_fields=(
            "iot_temperature",
            "cargo_category",
        ),
        applicability_note=(
            "The dataset does not contain cargo_category. "
            "This rule cannot be evaluated reliably until cargo "
            "type is supplied by a verified operational source."
        ),
    ),

    "CC-003": RuleDefinition(
        rule_id="CC-003",
        name="LA/Long Beach Port Congestion Diversion",
        description=(
            "Identify shipments associated with LA or Long Beach "
            "where port congestion exceeds 7."
        ),
        severity=Severity.HIGH,
        required_fields=(
            "port_congestion_level",
            "port_name",
        ),
        applicability_note=(
            "The dataset does not contain port_name. "
            "This rule cannot be evaluated reliably until port "
            "identity is supplied by a verified operational source."
        ),
    ),
}


def get_rule(rule_id: str) -> RuleDefinition:
    """Retrieve a rule definition by its ID."""

    try:
        return RULE_REGISTRY[rule_id]
    except KeyError:
        raise ValueError(f"Unknown rule ID: {rule_id}") from None


def get_all_rules() -> list[RuleDefinition]:
    """Return all registered operational rules."""

    return list(RULE_REGISTRY.values())
