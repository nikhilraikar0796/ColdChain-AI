
from getpass import getpass

import pyodbc

from ingest_to_sqlserver import (
    load_and_validate_data,
    prepare_record,
)


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "sa"


def main():

    print("Loading cleaned source dataset...")

    df = load_and_validate_data()

    # Generate the expected hashes using exactly
    # the same normalization as the ingestion pipeline.

    expected_hashes = {
        prepare_record(row)[0]
        for row in df.itertuples(index=False, name=None)
    }

    expected_risk_counts = {
        str(key): int(value)
        for key, value in
        df["risk_classification"].value_counts().items()
    }

    password = getpass("SQL Server password: ")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    connection = pyodbc.connect(
        connection_string,
        timeout=15
    )

    cursor = connection.cursor()

    try:

        # Compare complete source-record fingerprints.

        cursor.execute("""
            SELECT source_record_hash
            FROM dbo.shipment_telemetry
        """)

        actual_hashes = {
            row[0].strip()
            for row in cursor.fetchall()
        }

        missing_hashes = expected_hashes - actual_hashes
        unexpected_hashes = actual_hashes - expected_hashes

        # Compare risk classification distributions.

        cursor.execute("""
            SELECT risk_classification, COUNT(*)
            FROM dbo.shipment_telemetry
            GROUP BY risk_classification
        """)

        actual_risk_counts = {
            str(row[0]): int(row[1])
            for row in cursor.fetchall()
        }

        # Compare timestamp boundaries.

        cursor.execute("""
            SELECT
                COUNT(*),
                MIN(recorded_at),
                MAX(recorded_at)
            FROM dbo.shipment_telemetry
        """)

        db_count, db_min, db_max = cursor.fetchone()

        source_min = df["timestamp"].min().to_pydatetime()
        source_max = df["timestamp"].max().to_pydatetime()

        # Display results.

        print("\n========== DATA INTEGRITY REPORT ==========")

        print("Source records:", len(df))
        print("Database records:", db_count)

        print("Expected unique hashes:", len(expected_hashes))
        print("Actual unique hashes:", len(actual_hashes))

        print("Missing source records:", len(missing_hashes))
        print("Unexpected database records:", len(unexpected_hashes))

        print("\nRisk classification comparison:")

        for risk in sorted(expected_risk_counts):

            expected = expected_risk_counts[risk]
            actual = actual_risk_counts.get(risk, 0)

            print(
                f"{risk}: Source={expected}, Database={actual}"
            )

        print("\nTimestamp comparison:")

        print("Source earliest:", source_min)
        print("Database earliest:", db_min)

        print("Source latest:", source_max)
        print("Database latest:", db_max)

        # Final assertions.

        checks = {
            "Record count": len(df) == db_count,
            "Hash count": len(expected_hashes) == len(actual_hashes),
            "All source hashes found": len(missing_hashes) == 0,
            "No unexpected hashes": len(unexpected_hashes) == 0,
            "Risk distributions": expected_risk_counts == actual_risk_counts,
            "Earliest timestamp": source_min == db_min,
            "Latest timestamp": source_max == db_max,
        }

        print("\n========== FINAL CHECKS ==========")

        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")

        if not all(checks.values()):
            raise RuntimeError(
                "Database integrity verification failed."
            )

        print("\nDATABASE INTEGRITY: SUCCESS")

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
