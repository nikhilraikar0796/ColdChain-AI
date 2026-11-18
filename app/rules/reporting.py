
import csv
import json

from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path

from app.rules.models import RuleResult


def _json_default(value):
    """Convert non-standard Python values into JSON-compatible values."""

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, datetime):
        return value.isoformat()

    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )


def write_evaluation_report(
    results: list[RuleResult],
    records_evaluated: int,
    sql_tier2_ids: set,
    python_tier2_ids: set,
    output_dir: str = "data/processed",
):
    """Generate JSON evaluation report and CSV triggered-alert report."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    counts = Counter(
        (result.rule_id, result.status.value)
        for result in results
    )

    rule_ids = ("CC-001", "CC-002", "CC-003")

    rule_summaries = []

    for rule_id in rule_ids:
        rule_summaries.append({
            "rule_id": rule_id,
            "triggered": counts[(rule_id, "triggered")],
            "not_triggered": counts[(rule_id, "not_triggered")],
            "not_evaluable": counts[(rule_id, "not_evaluable")],
        })

    triggered_alerts = [
        result for result in results
        if result.status.value == "triggered"
    ]

    missing_ids = sql_tier2_ids - python_tier2_ids
    extra_ids = python_tier2_ids - sql_tier2_ids

    report = {
        "metadata": {
            "generated_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "source_view": "agent_views.vw_telemetry_overview",
            "records_evaluated": records_evaluated,
            "rules_per_record": len(rule_ids),
            "total_rule_evaluations": len(results),
        },

        "rule_summaries": rule_summaries,

        "sql_validation": {
            "rule_id": "CC-001",
            "sql_candidate_count": len(sql_tier2_ids),
            "python_candidate_count": len(python_tier2_ids),
            "missing_in_python": len(missing_ids),
            "extra_in_python": len(extra_ids),
            "record_level_match": (
                not missing_ids and not extra_ids
            ),
        },

        "triggered_alerts": [
            asdict(alert)
            for alert in triggered_alerts
        ],
    }

    json_path = output_path / "rule_evaluation_report.json"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            default=_json_default,
        )

    csv_path = output_path / "triggered_alerts.csv"

    csv_fields = [
        "record_id",
        "rule_id",
        "rule_name",
        "severity",
        "message",
        "recommended_action",
        "evidence",
        "limitations",
    ]

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=csv_fields,
        )

        writer.writeheader()

        for alert in triggered_alerts:
            writer.writerow({
                "record_id": alert.record_id,
                "rule_id": alert.rule_id,
                "rule_name": alert.rule_name,
                "severity": (
                    alert.severity.value
                    if alert.severity else ""
                ),
                "message": alert.message,
                "recommended_action": alert.recommended_action,
                "evidence": json.dumps(
                    alert.evidence,
                    default=_json_default,
                ),
                "limitations": json.dumps(alert.limitations),
            })

    return json_path, csv_path
