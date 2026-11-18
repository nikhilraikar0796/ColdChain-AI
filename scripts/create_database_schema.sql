
-- ============================================================
-- ColdChain-AI: SQL Server database schema
-- Database: ColdChainDB
-- Purpose: Store validated cold-chain telemetry records
-- ============================================================

IF OBJECT_ID(N'dbo.shipment_telemetry', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.shipment_telemetry
    (
        telemetry_id BIGINT IDENTITY(1,1) NOT NULL,

        -- Ingestion metadata
        source_record_hash CHAR(64) NOT NULL,

        -- Source timestamp is renamed to avoid SQL Server's
        -- legacy TIMESTAMP/ROWVERSION data-type terminology.
        recorded_at DATETIME2(0) NOT NULL,

        -- Geographic information
        vehicle_gps_latitude DECIMAL(10,7) NOT NULL,
        vehicle_gps_longitude DECIMAL(10,7) NOT NULL,

        -- Operational measurements
        fuel_consumption_rate DECIMAL(18,6) NOT NULL,
        eta_variation_hours DECIMAL(18,6) NOT NULL,
        traffic_congestion_level DECIMAL(18,6) NOT NULL,
        warehouse_inventory_level DECIMAL(18,6) NOT NULL,
        loading_unloading_time DECIMAL(18,6) NOT NULL,
        handling_equipment_availability DECIMAL(18,6) NOT NULL,
        order_fulfillment_status DECIMAL(18,6) NOT NULL,
        weather_condition_severity DECIMAL(18,6) NOT NULL,
        port_congestion_level DECIMAL(18,6) NOT NULL,
        shipping_costs DECIMAL(18,6) NOT NULL,
        supplier_reliability_score DECIMAL(18,6) NOT NULL,
        lead_time_days DECIMAL(18,6) NOT NULL,
        historical_demand DECIMAL(18,6) NOT NULL,
        iot_temperature DECIMAL(18,6) NOT NULL,
        cargo_condition_status DECIMAL(18,6) NOT NULL,
        route_risk_level DECIMAL(18,6) NOT NULL,
        customs_clearance_time DECIMAL(18,6) NOT NULL,
        driver_behavior_score DECIMAL(18,6) NOT NULL,
        fatigue_monitoring_score DECIMAL(18,6) NOT NULL,
        disruption_likelihood_score DECIMAL(18,6) NOT NULL,
        delay_probability DECIMAL(18,6) NOT NULL,

        -- Categorical information
        risk_classification NVARCHAR(30) NOT NULL,

        -- Delivery outcome measurement
        delivery_time_deviation DECIMAL(18,6) NOT NULL,

        -- Primary key
        CONSTRAINT PK_shipment_telemetry
            PRIMARY KEY CLUSTERED (telemetry_id),

        -- Prevent duplicate ingestion of the same source record
        CONSTRAINT UQ_shipment_telemetry_source_hash
            UNIQUE (source_record_hash),

        -- Geographic validation
        CONSTRAINT CK_telemetry_latitude
            CHECK (vehicle_gps_latitude BETWEEN -90 AND 90),

        CONSTRAINT CK_telemetry_longitude
            CHECK (vehicle_gps_longitude BETWEEN -180 AND 180),

        -- Score validation
        CONSTRAINT CK_telemetry_probability_scores
            CHECK (
                handling_equipment_availability BETWEEN 0 AND 1
                AND order_fulfillment_status BETWEEN 0 AND 1
                AND weather_condition_severity BETWEEN 0 AND 1
                AND supplier_reliability_score BETWEEN 0 AND 1
                AND cargo_condition_status BETWEEN 0 AND 1
                AND driver_behavior_score BETWEEN 0 AND 1
                AND fatigue_monitoring_score BETWEEN 0 AND 1
                AND disruption_likelihood_score BETWEEN 0 AND 1
                AND delay_probability BETWEEN 0 AND 1
            ),

        -- Congestion and route-risk validation
        CONSTRAINT CK_telemetry_congestion_scores
            CHECK (
                traffic_congestion_level BETWEEN 0 AND 10
                AND port_congestion_level BETWEEN 0 AND 10
                AND route_risk_level BETWEEN 0 AND 10
            ),

        -- Risk classification validation
        CONSTRAINT CK_telemetry_risk_classification
            CHECK (
                risk_classification IN (
                    N'Low Risk',
                    N'Moderate Risk',
                    N'High Risk'
                )
            )
    );

    PRINT 'Table dbo.shipment_telemetry created successfully.';
END
ELSE
BEGIN
    PRINT 'Table dbo.shipment_telemetry already exists. No changes made.';
END;
