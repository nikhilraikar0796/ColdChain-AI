
import getpass

import pyodbc


# ============================================================
# COLDCHAIN-AI: SEMANTIC SQL LAYER
# Database: ColdChainDB
# Schema: agent_views
# ============================================================

SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"
USERNAME = "sa"


# Each SQL statement is executed separately.
# This avoids SQL Server's CREATE VIEW batch restrictions.

CREATE_SCHEMA_SQL = """
IF SCHEMA_ID(N'agent_views') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA agent_views');
END;
"""


# ============================================================
# VIEW 1: GENERAL TELEMETRY OVERVIEW
# ============================================================

CREATE_OVERVIEW_VIEW_SQL = """
CREATE OR ALTER VIEW agent_views.vw_telemetry_overview
AS
SELECT
    telemetry_id,
    recorded_at,

    vehicle_gps_latitude AS latitude,
    vehicle_gps_longitude AS longitude,

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

FROM dbo.shipment_telemetry;
"""


# ============================================================
# VIEW 2: TIER 2 ESCALATION CANDIDATES
# SOP CONDITION:
# High Risk AND delay_probability > 0.65
#
# This identifies matching conditions, not actual
# recorded operational escalations.
# ============================================================

CREATE_TIER2_VIEW_SQL = """
CREATE OR ALTER VIEW agent_views.vw_tier2_escalation_candidates
AS
SELECT
    telemetry_id,
    recorded_at,

    latitude = vehicle_gps_latitude,
    longitude = vehicle_gps_longitude,

    risk_classification,
    delay_probability,
    eta_variation_hours,
    disruption_likelihood_score,

    CAST(1 AS BIT) AS tier2_escalation_condition_met,

    CAST(
        N'Actual escalation status is not recorded in source data'
        AS NVARCHAR(100)
    ) AS escalation_status_note

FROM dbo.shipment_telemetry

WHERE
    risk_classification = N'High Risk'
    AND delay_probability > 0.65;
"""


# ============================================================
# VIEW 3: TEMPERATURE REVIEW CANDIDATES
# SOP THRESHOLD:
# Temperature above 4 degrees Celsius.
#
# Cargo category is missing, so applicability to
# fresh perishables cannot be established.
# ============================================================

CREATE_TEMPERATURE_VIEW_SQL = """
CREATE OR ALTER VIEW agent_views.vw_temperature_review_candidates
AS
SELECT
    telemetry_id,
    recorded_at,

    latitude = vehicle_gps_latitude,
    longitude = vehicle_gps_longitude,

    iot_temperature,
    eta_variation_hours,
    risk_classification,
    delay_probability,

    CAST(1 AS BIT) AS temperature_above_4c,

    CAST(
        N'Cargo category unavailable; SOP applicability unverified'
        AS NVARCHAR(100)
    ) AS applicability_note

FROM dbo.shipment_telemetry

WHERE iot_temperature > 4.0;
"""


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():

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

    cursor = connection.cursor()

    try:

        print("Creating semantic schema...")

        cursor.execute(CREATE_SCHEMA_SQL)

        print("Creating telemetry overview view...")

        cursor.execute(CREATE_OVERVIEW_VIEW_SQL)

        print("Creating Tier 2 escalation view...")

        cursor.execute(CREATE_TIER2_VIEW_SQL)

        print("Creating temperature review view...")

        cursor.execute(CREATE_TEMPERATURE_VIEW_SQL)

        connection.commit()

        print("\nSemantic SQL layer created successfully.")

        # Verify view definitions are registered.

        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_SCHEMA = 'agent_views'
            ORDER BY TABLE_NAME
        """)

        print("\nCreated views:")

        for row in cursor.fetchall():
            print(f"{row[0]}.{row[1]}")

    except Exception:

        connection.rollback()

        print("\nSemantic layer creation failed.")
        raise

    finally:

        cursor.close()
        connection.close()

        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
