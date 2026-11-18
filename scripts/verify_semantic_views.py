
import getpass

import pyodbc


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "sa"


def main():

    password = getpass.getpass("SQL Server password: ")

    connection = pyodbc.connect(
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;",
        timeout=15
    )

    cursor = connection.cursor()

    try:

        checks = [
            (
                "Telemetry overview",
                """
                SELECT COUNT(*)
                FROM agent_views.vw_telemetry_overview
                """
            ),
            (
                "Tier 2 escalation candidates",
                """
                SELECT COUNT(*)
                FROM agent_views.vw_tier2_escalation_candidates
                """
            ),
            (
                "Temperature review candidates",
                """
                SELECT COUNT(*)
                FROM agent_views.vw_temperature_review_candidates
                """
            )
        ]

        print("\n========== SEMANTIC VIEW VERIFICATION ==========")

        for name, query in checks:

            cursor.execute(query)

            count = cursor.fetchone()[0]

            print(f"{name}: {count:,} records")

        # Verify the actual Tier 2 condition.

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.shipment_telemetry
            WHERE risk_classification = N'High Risk'
              AND delay_probability > 0.65
        """)

        expected_tier2 = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM agent_views.vw_tier2_escalation_candidates
        """)

        actual_tier2 = cursor.fetchone()[0]

        print("\nTier 2 rule comparison:")
        print("Expected:", expected_tier2)
        print("View:", actual_tier2)

        if expected_tier2 != actual_tier2:
            raise RuntimeError("Tier 2 view verification failed.")

        print("\nSEMANTIC VIEW VERIFICATION: SUCCESS")

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
