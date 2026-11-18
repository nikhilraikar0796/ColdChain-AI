
import hashlib
import json
import getpass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd
import pyodbc


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "cleaned_supply_chain_data.csv"
)

BATCH_SIZE = 1000

SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "sa"

TABLE_NAME = "dbo.shipment_telemetry"

EXPECTED_COLUMNS = [
    "timestamp",
    "vehicle_gps_latitude",
    "vehicle_gps_longitude",
    "fuel_consumption_rate",
    "eta_variation_hours",
    "traffic_congestion_level",
    "warehouse_inventory_level",
    "loading_unloading_time",
    "handling_equipment_availability",
    "order_fulfillment_status",
    "weather_condition_severity",
    "port_congestion_level",
    "shipping_costs",
    "supplier_reliability_score",
    "lead_time_days",
    "historical_demand",
    "iot_temperature",
    "cargo_condition_status",
    "route_risk_level",
    "customs_clearance_time",
    "driver_behavior_score",
    "fatigue_monitoring_score",
    "disruption_likelihood_score",
    "delay_probability",
    "risk_classification",
    "delivery_time_deviation",
]

NUMERIC_COLUMNS = [
    column
    for column in EXPECTED_COLUMNS
    if column not in ["timestamp", "risk_classification"]
]

INSERT_SQL = """
INSERT INTO dbo.shipment_telemetry (
    source_record_hash,
    recorded_at,
    vehicle_gps_latitude,
    vehicle_gps_longitude,
    fuel_consumption_rate,
    eta_variation_hours,
    traffic_congestion_level,
    warehouse_inventory_level,
    loading_unloading_time,
    handling_equipment_availability,
    order_fulfillment_status,
    weather_condition_severity,
    port_congestion_level,
    shipping_costs,
    supplier_reliability_score,
    lead_time_days,
    historical_demand,
    iot_temperature,
    cargo_condition_status,
    route_risk_level,
    customs_clearance_time,
    driver_behavior_score,
    fatigue_monitoring_score,
    disruption_likelihood_score,
    delay_probability,
    risk_classification,
    delivery_time_deviation
)
VALUES (
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
)
"""


# ============================================================
# 2. DATA VALIDATION
# ============================================================

def load_and_validate_data():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found: {CSV_PATH}"
        )

    df = pd.read_csv(CSV_PATH)

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            "Dataset columns do not match the expected schema."
        )

    if df.empty:
        raise ValueError("Dataset is empty.")

    if df.isna().any().any():
        raise ValueError(
            "Dataset contains missing values."
        )

    if df.duplicated().any():
        raise ValueError(
            "Dataset contains duplicate records."
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    valid_risk_values = {
        "Low Risk",
        "Moderate Risk",
        "High Risk",
    }

    if not set(df["risk_classification"]).issubset(
        valid_risk_values
    ):
        raise ValueError(
            "Unexpected risk classification found."
        )

    print("Dataset validation successful.")
    print("Records:", len(df))
    print("Columns:", len(df.columns))

    return df


# ============================================================
# 3. NORMALIZE VALUES AND GENERATE RECORD HASH
# ============================================================

def normalize_decimal(value):

    return Decimal(str(value)).quantize(
        Decimal("0.000001"),
        rounding=ROUND_HALF_UP
    )


def prepare_record(row):

    timestamp = pd.Timestamp(
        row[0]
    ).to_pydatetime()

    risk_classification = str(row[24])

    normalized_numeric_values = [
        normalize_decimal(value)
        for value in row[1:24]
    ]

    final_numeric_value = normalize_decimal(row[25])

    # Hash the normalized database representation.
    # This ensures the same record gets the same hash
    # even when the script is executed again.

    canonical_values = [
        timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    ]

    canonical_values.extend(
        format(value, "f")
        for value in normalized_numeric_values
    )

    canonical_values.append(risk_classification)

    canonical_values.append(
        format(final_numeric_value, "f")
    )

    canonical_json = json.dumps(
        canonical_values,
        separators=(",", ":"),
        ensure_ascii=False
    )

    record_hash = hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()

    sql_record = (
        record_hash,
        timestamp,
        *normalized_numeric_values,
        risk_classification,
        final_numeric_value,
    )

    return record_hash, sql_record


# ============================================================
# 4. DATABASE CONNECTION
# ============================================================

def connect_to_database():

    password = getpass.getpass(
        "SQL Server password: "
    )

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

    print("Connected to SQL Server.")
    print("Database:", DATABASE)

    return connection


# ============================================================
# 5. INGESTION
# ============================================================

def ingest_data(df, connection):

    cursor = connection.cursor()

    try:

        # Retrieve existing hashes to support safe reruns.

        cursor.execute(
            """
            SELECT source_record_hash
            FROM dbo.shipment_telemetry
            """
        )

        existing_hashes = {
            row[0].strip()
            for row in cursor.fetchall()
        }

        print(
            "Existing database records:",
            len(existing_hashes)
        )

        records_to_insert = []

        for row in df.itertuples(
            index=False,
            name=None
        ):

            record_hash, sql_record = prepare_record(row)

            if record_hash not in existing_hashes:

                records_to_insert.append(sql_record)

                # Also prevent duplicates within this
                # current ingestion batch.

                existing_hashes.add(record_hash)

        print(
            "New records to insert:",
            len(records_to_insert)
        )

        if not records_to_insert:

            print("No new records found.")
            return 0

        cursor.fast_executemany = True

        inserted_count = 0

        for start in range(
            0,
            len(records_to_insert),
            BATCH_SIZE
        ):

            batch = records_to_insert[
                start:start + BATCH_SIZE
            ]

            cursor.executemany(
                INSERT_SQL,
                batch
            )

            inserted_count += len(batch)

            print(
                f"Inserted in current transaction: "
                f"{inserted_count}/{len(records_to_insert)}"
            )

        # Commit only after all batches succeed.

        connection.commit()

        print("Database transaction committed.")

        return inserted_count

    except Exception:

        connection.rollback()

        print(
            "Ingestion failed. Transaction rolled back."
        )

        raise

    finally:

        cursor.close()


# ============================================================
# 6. DATABASE VERIFICATION
# ============================================================

def verify_database(connection):

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_records,
            COUNT(DISTINCT source_record_hash) AS unique_hashes,
            MIN(recorded_at) AS earliest_record,
            MAX(recorded_at) AS latest_record
        FROM dbo.shipment_telemetry
        """
    )

    result = cursor.fetchone()

    print("\n========== DATABASE VERIFICATION ==========")

    print("Total records:", result[0])
    print("Unique record hashes:", result[1])
    print("Earliest timestamp:", result[2])
    print("Latest timestamp:", result[3])

    if result[0] != result[1]:
        raise RuntimeError(
            "Duplicate source hashes detected."
        )

    cursor.close()


# ============================================================
# 7. MAIN EXECUTION
# ============================================================

def main():

    connection = None

    try:

        print("Loading cleaned dataset...\n")

        df = load_and_validate_data()

        print("\nConnecting to database...\n")

        connection = connect_to_database()

        print("\nStarting ingestion...\n")

        inserted_count = ingest_data(
            df,
            connection
        )

        verify_database(connection)

        print("\n========== INGESTION SUMMARY ==========")
        print("New records inserted:", inserted_count)
        print("Source records:", len(df))
        print("Ingestion status: SUCCESS")

    except Exception as error:

        print("\nINGESTION ERROR:")
        print(str(error))

        raise

    finally:

        if connection is not None:
            connection.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
