
import getpass
import pyodbc


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "coldchain_agent_login"

VIEWS = [
    "vw_telemetry_overview",
    "vw_tier2_escalation_candidates",
    "vw_temperature_review_candidates",
]


def main():
    password = getpass.getpass("SQL Server agent password: ")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={{{password}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=10;"
    )

    print("\nConnecting with the restricted agent account...")

    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()

        print("\n========== AGENT VIEW SCHEMA ==========")

        for view_name in VIEWS:
            query = f"SELECT TOP (0) * FROM agent_views.[{view_name}]"
            cursor.execute(query)

            columns = [
                column[0]
                for column in cursor.description
            ]

            print(f"\nView: agent_views.{view_name}")
            print("-" * 45)

            for column in columns:
                print(f"- {column}")

        print("\nSchema inspection completed successfully.")


if __name__ == "__main__":
    main()
