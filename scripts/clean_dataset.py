
from pathlib import Path
import json

import pandas as pd


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CLEANED_FILE = PROCESSED_DIR / "cleaned_supply_chain_data.csv"
REPORT_FILE = PROCESSED_DIR / "data_quality_report.json"
REJECTED_FILE = PROCESSED_DIR / "rejected_records.csv"


# --------------------------------------------------
# 2. EXPECTED DATASET SCHEMA
# --------------------------------------------------

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

PROBABILITY_COLUMNS = [
    "handling_equipment_availability",
    "order_fulfillment_status",
    "weather_condition_severity",
    "supplier_reliability_score",
    "cargo_condition_status",
    "driver_behavior_score",
    "fatigue_monitoring_score",
    "disruption_likelihood_score",
    "delay_probability",
]

VALID_RISK_CLASSES = {
    "Low Risk",
    "Moderate Risk",
    "High Risk",
}


# --------------------------------------------------
# 3. MAIN CLEANING FUNCTION
# --------------------------------------------------

def clean_dataset():

    print("\n========== COLDCHAIN DATA CLEANING ==========\n")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_FILE}"
        )

    # Read original data
    df = pd.read_csv(
        RAW_FILE,
        encoding="utf-8-sig",
        low_memory=False
    )

    original_rows = len(df)

    print(f"Original records: {original_rows}")
    print(f"Original columns: {len(df.columns)}")

    # --------------------------------------------------
    # 4. SCHEMA VALIDATION
    # --------------------------------------------------

    missing_columns = [
        col for col in EXPECTED_COLUMNS
        if col not in df.columns
    ]

    unexpected_columns = [
        col for col in df.columns
        if col not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing: {missing_columns}"
        )

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns found: {unexpected_columns}"
        )

    # Standardize column order
    df = df[EXPECTED_COLUMNS].copy()

    # Track rejection reasons for every record
    rejection_reasons = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    def add_rejection(condition, reason):
        nonlocal rejection_reasons

        condition = condition.fillna(False)

        rejection_reasons.loc[condition] = (
            rejection_reasons.loc[condition]
            .apply(
                lambda existing: (
                    f"{existing}; {reason}"
                    if existing
                    else reason
                )
            )
        )

    # --------------------------------------------------
    # 5. TIMESTAMP VALIDATION
    # --------------------------------------------------

    original_timestamps = df["timestamp"].copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    invalid_timestamps = df["timestamp"].isna()

    add_rejection(
        invalid_timestamps,
        "invalid_timestamp"
    )

    # --------------------------------------------------
    # 6. NUMERIC DATA VALIDATION
    # --------------------------------------------------

    numeric_conversion_failures = {}

    for column in NUMERIC_COLUMNS:

        original_values = df[column].copy()

        converted = pd.to_numeric(
            original_values,
            errors="coerce"
        )

        failed = (
            original_values.notna()
            & converted.isna()
        )

        numeric_conversion_failures[column] = int(
            failed.sum()
        )

        add_rejection(
            failed,
            f"invalid_numeric_value:{column}"
        )

        df[column] = converted

        infinite_values = df[column].isin([
            float("inf"),
            float("-inf")
        ])

        add_rejection(
            infinite_values,
            f"infinite_value:{column}"
        )

    # --------------------------------------------------
    # 7. MISSING VALUE VALIDATION
    # --------------------------------------------------

    missing_value_counts = (
        df[EXPECTED_COLUMNS]
        .isna()
        .sum()
        .to_dict()
    )

    for column in EXPECTED_COLUMNS:

        add_rejection(
            df[column].isna(),
            f"missing_value:{column}"
        )

    # --------------------------------------------------
    # 8. UNIVERSAL NUMERIC RANGE VALIDATION
    # --------------------------------------------------

    # Geographic coordinate limits
    add_rejection(
        ~df["vehicle_gps_latitude"].between(-90, 90),
        "invalid_latitude"
    )

    add_rejection(
        ~df["vehicle_gps_longitude"].between(-180, 180),
        "invalid_longitude"
    )

    # Probability and score columns
    for column in PROBABILITY_COLUMNS:

        add_rejection(
            ~df[column].between(0, 1),
            f"outside_valid_score_range:{column}"
        )

    # --------------------------------------------------
    # 9. RISK CLASSIFICATION VALIDATION
    # --------------------------------------------------

    invalid_risk_classes = ~df[
        "risk_classification"
    ].isin(VALID_RISK_CLASSES)

    add_rejection(
        invalid_risk_classes,
        "invalid_risk_classification"
    )

    # --------------------------------------------------
    # 10. EXACT DUPLICATE VALIDATION
    # --------------------------------------------------

    duplicate_rows = df.duplicated(
        subset=EXPECTED_COLUMNS,
        keep="first"
    )

    add_rejection(
        duplicate_rows,
        "duplicate_full_row"
    )

    # --------------------------------------------------
    # 11. SEPARATE VALID AND REJECTED RECORDS
    # --------------------------------------------------

    rejected_mask = rejection_reasons.ne("")

    cleaned_df = df.loc[~rejected_mask].copy()

    rejected_df = df.loc[rejected_mask].copy()

    rejected_df["rejection_reasons"] = (
        rejection_reasons.loc[rejected_mask]
    )

    # --------------------------------------------------
    # 12. SAVE OUTPUT FILES
    # --------------------------------------------------

    cleaned_df.to_csv(
        CLEANED_FILE,
        index=False,
        encoding="utf-8"
    )

    if not rejected_df.empty:

        rejected_df.to_csv(
            REJECTED_FILE,
            index=False,
            encoding="utf-8"
        )

    # --------------------------------------------------
    # 13. DATA QUALITY REPORT
    # --------------------------------------------------

    report = {
        "source_file": str(RAW_FILE.name),
        "cleaned_file": str(CLEANED_FILE.name),
        "original_records": int(original_rows),
        "cleaned_records": int(len(cleaned_df)),
        "rejected_records": int(len(rejected_df)),
        "original_columns": int(len(df.columns)),
        "missing_values_by_column": {
            key: int(value)
            for key, value in missing_value_counts.items()
        },
        "numeric_conversion_failures": (
            numeric_conversion_failures
        ),
        "duplicate_rows_detected": int(
            duplicate_rows.sum()
        ),
        "invalid_timestamps": int(
            invalid_timestamps.sum()
        ),
        "rejection_reason_counts": {
            reason: int(
                rejection_reasons.str.contains(
                    reason,
                    regex=False
                ).sum()
            )
            for reason in [
                "invalid_timestamp",
                "invalid_latitude",
                "invalid_longitude",
                "invalid_risk_classification",
                "duplicate_full_row",
            ]
        },
        "cleaning_status": (
            "SUCCESS"
            if rejected_df.empty
            else "SUCCESS_WITH_REJECTIONS"
        ),
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    # --------------------------------------------------
    # 14. DISPLAY SUMMARY
    # --------------------------------------------------

    print("\n========== CLEANING SUMMARY ==========\n")

    print(f"Original records : {original_rows}")
    print(f"Cleaned records  : {len(cleaned_df)}")
    print(f"Rejected records : {len(rejected_df)}")

    print(
        "\nNumeric conversion failures:",
        sum(numeric_conversion_failures.values())
    )

    print(
        "Duplicate rows detected:",
        duplicate_rows.sum()
    )

    print(
        "\nCleaning status:",
        report["cleaning_status"]
    )

    print("\nGenerated files:")

    print(f"- {CLEANED_FILE}")

    print(f"- {REPORT_FILE}")

    if not rejected_df.empty:
        print(f"- {REJECTED_FILE}")
    else:
        print("- No rejected-record file needed.")

    print("\n======================================\n")


# --------------------------------------------------
# 15. SCRIPT ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    clean_dataset()
