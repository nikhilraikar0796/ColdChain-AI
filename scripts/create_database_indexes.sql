
-- ============================================================
-- ColdChain-AI: Database performance indexes
-- Database: ColdChainDB
-- Table: dbo.shipment_telemetry
-- ============================================================

-- 1. Date-range filtering
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_telemetry_recorded_at'
      AND object_id = OBJECT_ID(N'dbo.shipment_telemetry')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_telemetry_recorded_at
    ON dbo.shipment_telemetry (recorded_at);

    PRINT 'Created IX_telemetry_recorded_at.';
END
ELSE
BEGIN
    PRINT 'IX_telemetry_recorded_at already exists.';
END;


-- 2. Risk classification and escalation filtering
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'IX_telemetry_risk_delay'
      AND object_id = OBJECT_ID(N'dbo.shipment_telemetry')
)
BEGIN
    CREATE NONCLUSTERED INDEX IX_telemetry_risk_delay
    ON dbo.shipment_telemetry (
        risk_classification,
        delay_probability
    )
    INCLUDE (recorded_at);

    PRINT 'Created IX_telemetry_risk_delay.';
END
ELSE
BEGIN
    PRINT 'IX_telemetry_risk_delay already exists.';
END;
