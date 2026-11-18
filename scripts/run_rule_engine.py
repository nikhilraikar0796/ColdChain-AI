
import getpass
from collections import Counter

import pyodbc
from app.rules.reporting import write_evaluation_report
from app.rules.engine import ColdChainRuleEngine
from app.rules.models import RuleStatus


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "coldchain_agent_login"


QUERY = """
SELECT
    telemetry_id,
    risk_classification,
    delay_probability,
    iot_temperature,
    port_congestion_level
FROM agent_views.vw_telemetry_overview
ORDER BY telemetry_id;
"""


REFERENCE_QUERY = """
SELECT telemetry_id
FROM agent_views.vw_tier2_escalation_candidates;
"""


def get_connection():
    password = getpass.getpass("AI agent login password: ")

    # Escape closing braces in ODBC connection-string values.
    escaped_password = password.replace("}", "}}")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={{{escaped_password}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=15;"
    )

    return pyodbc.connect(connection_string)


def main():

    print("\nConnecting with the restricted agent account...")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Retrieve telemetry records.
        print("Reading telemetry from the semantic view...")

        cursor.execute(QUERY)

        columns = [
            column[0]
            for column in cursor.description
        ]

        records = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        # Retrieve SQL Server's Tier 2 candidate IDs.
        print("Reading SQL Tier 2 reference candidates...")

        cursor.execute(REFERENCE_QUERY)

        sql_tier2_ids = {
            row[0]
            for row in cursor.fetchall()
        }

    finally:
        connection.close()

    print(f"Records retrieved: {len(records):,}")

    # Initialize the rule engine.
    engine = ColdChainRuleEngine()

    status_counts = {
        rule_id: Counter()
        for rule_id in ("CC-001", "CC-002", "CC-003")
    }

    triggered_alerts = []
    all_results = []

    # Track exact Python Tier 2 candidate IDs.
    python_tier2_ids = set()

    # Evaluate every record against all registered rules.
    for record in records:

        summary = engine.evaluate_summary(record)
        all_results.extend(summary.results)

        for result in summary.results:

            status_counts[result.rule_id][
                result.status.value
            ] += 1

            if result.status == RuleStatus.TRIGGERED:

                triggered_alerts.append(result)

                if result.rule_id == "CC-001":
                    python_tier2_ids.add(result.record_id)

    # Display rule evaluation results.
    print("\n========== RULE ENGINE RESULTS ==========")

    for rule_id, counts in status_counts.items():

        print(f"\n{rule_id}")
        print(f"  Triggered:      {counts['triggered']:,}")
        print(f"  Not triggered:  {counts['not_triggered']:,}")
        print(f"  Not evaluable:  {counts['not_evaluable']:,}")

    # Compare exact SQL and Python candidate IDs.
    print("\n========== SQL CROSS-CHECK ==========")

    missing_in_python = sql_tier2_ids - python_tier2_ids
    extra_in_python = python_tier2_ids - sql_tier2_ids

    print(f"SQL Tier 2 candidates:       {len(sql_tier2_ids):,}")
    print(f"Python Tier 2 candidates:    {len(python_tier2_ids):,}")
    print(f"Missing in Python:           {len(missing_in_python):,}")
    print(f"Extra in Python:             {len(extra_in_python):,}")

    if not missing_in_python and not extra_in_python:
        print("CC-001 RECORD-LEVEL VALIDATION: PASSED")
    else:
        print("CC-001 RECORD-LEVEL VALIDATION: FAILED")

        if missing_in_python:
            print("Sample missing IDs:", sorted(missing_in_python)[:10])

        if extra_in_python:
            print("Sample extra IDs:", sorted(extra_in_python)[:10])

    # Display sample triggered alerts.
    print("\n========== SAMPLE TRIGGERED ALERTS ==========")

    for alert in triggered_alerts[:10]:

        print(
            f"\nRecord ID: {alert.record_id}"
            f"\nRule: {alert.rule_id} - {alert.rule_name}"
            f"\nSeverity: {alert.severity.value}"
            f"\nMessage: {alert.message}"
            f"\nRecommended action: {alert.recommended_action}"
        )

    # Final execution summary.
    print("\n========== EXECUTION SUMMARY ==========")

    print(f"Total records evaluated: {len(records):,}")
    print(f"Total rule evaluations:  {len(records) * 3:,}")
    print(f"Total triggered alerts:  {len(triggered_alerts):,}")

    print("\n========== GENERATING REPORTS ==========")

    json_path, csv_path = write_evaluation_report(
        results=all_results,
        records_evaluated=len(records),
        sql_tier2_ids=sql_tier2_ids,
        python_tier2_ids=python_tier2_ids,
    )

    print(f"JSON report: {json_path}")
    print(f"CSV alerts:  {csv_path}")

    print("\nREPORT GENERATION: SUCCESS")


if __name__ == "__main__":
    main()
