
import getpass
import pyodbc


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
LOGIN = "coldchain_agent_login"


def connect_as_agent():
    password = getpass.getpass("AI agent login password: ")

    # Escape closing braces in ODBC connection-string values.
    escaped_password = password.replace("}", "}}")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={LOGIN};"
        f"PWD={{{escaped_password}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=15;"
    )

    return pyodbc.connect(connection_string)


def main():
    print("Connecting using the restricted AI agent login...")

    connection = connect_as_agent()

    try:
        cursor = connection.cursor()

        print("\n========== VIEW ACCESS TEST ==========")

        views = [
            "agent_views.vw_telemetry_overview",
            "agent_views.vw_tier2_escalation_candidates",
            "agent_views.vw_temperature_review_candidates",
        ]

        for view in views:
            cursor.execute(f"SELECT COUNT(*) FROM {view}")
            count = cursor.fetchone()[0]

            print(f"{view}: {count:,} records - PASS")

        print("\n========== RAW TABLE ACCESS TEST ==========")

        cursor.execute(
            """
            SELECT HAS_PERMS_BY_NAME(
                'dbo.shipment_telemetry',
                'OBJECT',
                'SELECT'
            )
            """
        )

        raw_select_permission = cursor.fetchone()[0]

        if raw_select_permission == 1:
            raise AssertionError(
                "FAIL: Agent has direct SELECT permission on raw table."
            )

        try:
            cursor.execute(
                "SELECT TOP 1 * FROM dbo.shipment_telemetry"
            )
            cursor.fetchone()

            raise AssertionError(
                "FAIL: Agent successfully queried the raw table."
            )

        except pyodbc.Error:
            print("Direct raw table query blocked - PASS")

        print("\n========== WRITE PERMISSION TEST ==========")

        write_permissions = ["INSERT", "UPDATE", "DELETE", "ALTER"]

        for permission in write_permissions:
            cursor.execute(
                """
                SELECT HAS_PERMS_BY_NAME(
                    'dbo.shipment_telemetry',
                    'OBJECT',
                    ?
                )
                """,
                permission
            )

            granted = cursor.fetchone()[0]

            if granted == 1:
                raise AssertionError(
                    f"FAIL: Agent has {permission} permission."
                )

            print(f"{permission}: Not granted - PASS")

        print("\n========== FINAL SECURITY RESULT ==========")
        print("Semantic view access: PASS")
        print("Direct raw table access: BLOCKED")
        print("Write permissions: NOT GRANTED")
        print("AGENT SECURITY VERIFICATION: SUCCESS")

    finally:
        connection.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
