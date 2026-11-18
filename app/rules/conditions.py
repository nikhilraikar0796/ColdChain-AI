
from typing import Any

from app.rules.models import RuleStatus


def get_numeric_value(
    record: dict[str, Any],
    field: str,
) -> tuple[float | None, str | None]:
    """
    Safely retrieve a numeric value from a record.

    Returns:
        (value, error)
    """

    raw_value = record.get(field)

    if raw_value is None:
        return None, f"Required field '{field}' is missing."

    if isinstance(raw_value, bool):
        return None, f"Field '{field}' cannot be a boolean."

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None, f"Field '{field}' must contain a numeric value."

    if not __import__("math").isfinite(value):
        return None, f"Field '{field}' must be finite."

    return value, None


def evaluate_greater_than(
    record: dict[str, Any],
    field: str,
    threshold: float,
) -> tuple[RuleStatus, str]:
    """
    Evaluate whether a numeric field is strictly greater
    than the specified threshold.
    """

    value, error = get_numeric_value(record, field)

    if error:
        return RuleStatus.NOT_EVALUABLE, error

    if value > threshold:
        return (
            RuleStatus.TRIGGERED,
            f"{field} = {value} is greater than {threshold}.",
        )

    return (
        RuleStatus.NOT_TRIGGERED,
        f"{field} = {value} is not greater than {threshold}.",
    )


def evaluate_equals(
    record: dict[str, Any],
    field: str,
    expected_value: Any,
) -> tuple[RuleStatus, str]:
    """
    Evaluate whether a field equals an expected value.
    """

    if field not in record or record[field] is None:
        return (
            RuleStatus.NOT_EVALUABLE,
            f"Required field '{field}' is missing.",
        )

    actual_value = record[field]

    if str(actual_value).strip().casefold() == str(expected_value).strip().casefold():
        return (
            RuleStatus.TRIGGERED,
            f"{field} matches '{expected_value}'.",
        )

    return (
        RuleStatus.NOT_TRIGGERED,
        f"{field} does not match '{expected_value}'.",
    )


def combine_and(
    *statuses: RuleStatus,
) -> RuleStatus:
    """
    Combine multiple condition results using AND logic.

    A false condition takes precedence because an AND
    expression cannot be true if any condition is false.

    If no condition is false but at least one is unknown,
    the combined result is not evaluable.
    """

    if not statuses:
        return RuleStatus.NOT_EVALUABLE

    if RuleStatus.NOT_TRIGGERED in statuses:
        return RuleStatus.NOT_TRIGGERED

    if RuleStatus.NOT_EVALUABLE in statuses:
        return RuleStatus.NOT_EVALUABLE

    return RuleStatus.TRIGGERED
