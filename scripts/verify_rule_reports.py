
import csv
import json
from pathlib import Path


REPORT_DIR = Path("data/processed")

JSON_FILE = REPORT_DIR / "rule_evaluation_report.json"
CSV_FILE = REPORT_DIR / "triggered_alerts.csv"


def main():

    print("\n========== REPORT FILE CHECK ==========")

    assert JSON_FILE.exists(), "JSON report is missing."
    assert CSV_FILE.exists(), "CSV report is missing."

    print("JSON report: EXISTS")
    print("CSV report: EXISTS")

    with JSON_FILE.open("r", encoding="utf-8") as file:
        report = json.load(file)

    print("\n========== JSON REPORT VALIDATION ==========")

    metadata = report["metadata"]

    assert metadata["records_evaluated"] == 32065
    assert metadata["total_rule_evaluations"] == 96195

    print(f"Records evaluated: {metadata['records_evaluated']:,}")
    print(f"Rule evaluations:  {metadata['total_rule_evaluations']:,}")

    expected = {
        "CC-001": (15440, 16625, 0),
        "CC-002": (0, 23391, 8674),
        "CC-003": (0, 12499, 19566),
    }

    for rule in report["rule_summaries"]:

        rule_id = rule["rule_id"]

        actual = (
            rule["triggered"],
            rule["not_triggered"],
            rule["not_evaluable"],
        )

        assert actual == expected[rule_id], (
            f"{rule_id} counts do not match expected values."
        )

        print(
            f"{rule_id}: "
            f"Triggered={actual[0]:,}, "
            f"Not triggered={actual[1]:,}, "
            f"Not evaluable={actual[2]:,} - PASS"
        )

    validation = report["sql_validation"]

    assert validation["record_level_match"] is True
    assert validation["sql_candidate_count"] == 15440
    assert validation["python_candidate_count"] == 15440
    assert validation["missing_in_python"] == 0
    assert validation["extra_in_python"] == 0

    print("\nSQL record-level validation: PASS")

    assert len(report["triggered_alerts"]) == 15440

    print(
        f"JSON triggered alerts: "
        f"{len(report['triggered_alerts']):,} - PASS"
    )

    print("\n========== CSV REPORT VALIDATION ==========")

    with CSV_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)
        alerts = list(reader)

    assert len(alerts) == 15440
    assert all(alert["rule_id"] == "CC-001" for alert in alerts)

    print(f"CSV alert records: {len(alerts):,} - PASS")
    print("CSV rule IDs: CC-001 only - PASS")

    print("\n========== FINAL RESULT ==========")
    print("ALL REPORT VALIDATION TESTS PASSED")


if __name__ == "__main__":
    main()
