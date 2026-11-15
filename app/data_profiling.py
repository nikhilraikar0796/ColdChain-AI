
from pathlib import Path
import json
import sys

import pandas as pd


# ---------------------------------------------------------
# 1. PROJECT PATHS AND CONFIGURATION
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_PATH = OUTPUT_DIR / "data_profile.json"

# Important business columns in our cold-chain dataset.
EXPECTED_COLUMNS = [
    "timestamp",
    "vehicle_gps_latitude",
    "vehicle_gps_longitude",
    "iot_temperature",
    "cargo_condition_status",
    "risk_classification",
    "delay_probability",
    "port_congestion_level",
    "route_risk_level",
]


# ---------------------------------------------------------
# 2. LOAD DATASET
# ---------------------------------------------------------

def load_dataset() -> pd.DataFrame:
    """Load the original logistics dataset."""

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    print("\nLoading logistics dataset...")

    df = pd.read_csv(
        DATASET_PATH,
        encoding="utf-8-sig",
        low_memory=False
    )

    print("Dataset loaded successfully.")

    return df


# ---------------------------------------------------------
# 3. BASIC DATASET INFORMATION
# ---------------------------------------------------------

def get_basic_information(df: pd.DataFrame) -> dict:
    """Return basic information about the dataset."""

    return {
        "total_rows": int(df.shape[0]),
        "total_columns": int(df.shape[1]),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / (1024 ** 2),
            2
        ),
        "column_names": df.columns.tolist(),
    }


# ---------------------------------------------------------
# 4. DATA QUALITY ANALYSIS
# ---------------------------------------------------------

def get_data_quality_report(df: pd.DataFrame) -> dict:
    """Identify missing values, duplicates and data types."""

    missing_values = df.isnull().sum()

    missing_report = {
        column: int(count)
        for column, count in missing_values.items()
        if count > 0
    }

    missing_percentage = {
        column: round(
            (count / len(df)) * 100, 2
        )
        for column, count in missing_report.items()
    }

    data_types = {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }

    return {
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_value_count": int(missing_values.sum()),
        "columns_with_missing_values": missing_report,
        "missing_percentage": missing_percentage,
        "data_types": data_types,
        "required_columns_missing": [
            column
            for column in EXPECTED_COLUMNS
            if column not in df.columns
        ],
    }


# ---------------------------------------------------------
# 5. NUMERICAL COLUMN ANALYSIS
# ---------------------------------------------------------

def get_numerical_analysis(df: pd.DataFrame) -> dict:
    """Generate descriptive statistics for numeric columns."""

    numerical_df = df.select_dtypes(include="number")

    if numerical_df.empty:
        return {}

    statistics = numerical_df.describe().round(3)

    return {
        column: {
            statistic: float(value)
            for statistic, value in statistics[column].items()
        }
        for column in statistics.columns
    }


# ---------------------------------------------------------
# 6. CATEGORICAL COLUMN ANALYSIS
# ---------------------------------------------------------

def get_categorical_analysis(df: pd.DataFrame) -> dict:
    """Analyse categorical values and their frequencies."""

    categorical_df = df.select_dtypes(
        include=["object", "category", "bool", "str"]
    )

    report = {}

    for column in categorical_df.columns:

        counts = (
            categorical_df[column]
            .value_counts(dropna=False)
            .head(10)
        )

        report[column] = {
            str(value): int(count)
            for value, count in counts.items()
        }

    return report


# ---------------------------------------------------------
# 7. BUSINESS-SPECIFIC VALIDATION
# ---------------------------------------------------------

def get_business_validation(df: pd.DataFrame) -> dict:
    """Check basic validity of important logistics fields."""

    report = {}

    # Validate GPS coordinates.
    if "vehicle_gps_latitude" in df.columns:
        latitude = pd.to_numeric(
            df["vehicle_gps_latitude"],
            errors="coerce"
        )

        report["invalid_latitude_count"] = int(
            (
                latitude.notna()
                & ~latitude.between(-90, 90)
            ).sum()
        )

        report["unparseable_latitude_count"] = int(
            (
                df["vehicle_gps_latitude"].notna()
                & latitude.isna()
            ).sum()
        )

    if "vehicle_gps_longitude" in df.columns:
        longitude = pd.to_numeric(
            df["vehicle_gps_longitude"],
            errors="coerce"
        )

        report["invalid_longitude_count"] = int(
            (
                longitude.notna()
                & ~longitude.between(-180, 180)
            ).sum()
        )

        report["unparseable_longitude_count"] = int(
            (
                df["vehicle_gps_longitude"].notna()
                & longitude.isna()
            ).sum()
        )

    # Delay probability should be between 0 and 1.
    if "delay_probability" in df.columns:
        probability = pd.to_numeric(
            df["delay_probability"],
            errors="coerce"
        )

        report["invalid_delay_probability_count"] = int(
            (
                probability.notna()
                & ~probability.between(0, 1)
            ).sum()
        )

        report["unparseable_delay_probability_count"] = int(
            (
                df["delay_probability"].notna()
                & probability.isna()
            ).sum()
        )

    # Inspect timestamps without assuming a timezone.
    if "timestamp" in df.columns:
        timestamps = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        report["invalid_timestamp_count"] = int(
            (
                df["timestamp"].notna()
                & timestamps.isna()
            ).sum()
        )

        valid_timestamps = timestamps.dropna()

        if not valid_timestamps.empty:
            report["earliest_timestamp"] = str(
                valid_timestamps.min()
            )

            report["latest_timestamp"] = str(
                valid_timestamps.max()
            )

    # Temperature is reported, not judged against an
    # arbitrary threshold. Actual limits must come from SOP.
    if "iot_temperature" in df.columns:
        temperature = pd.to_numeric(
            df["iot_temperature"],
            errors="coerce"
        )

        report["temperature_unparseable_count"] = int(
            (
                df["iot_temperature"].notna()
                & temperature.isna()
            ).sum()
        )

        if temperature.notna().any():
            report["temperature_min"] = float(
                temperature.min()
            )

            report["temperature_max"] = float(
                temperature.max()
            )

            report["temperature_mean"] = round(
                float(temperature.mean()), 3
            )

    return report


# ---------------------------------------------------------
# 8. GENERATE COMPLETE REPORT
# ---------------------------------------------------------

def generate_profile(df: pd.DataFrame) -> dict:
    """Combine all profiling results into one report."""

    return {
        "project": "ColdChain-AI",
        "dataset": DATASET_PATH.name,
        "basic_information": get_basic_information(df),
        "data_quality": get_data_quality_report(df),
        "numerical_analysis": get_numerical_analysis(df),
        "categorical_analysis": get_categorical_analysis(df),
        "business_validation": get_business_validation(df),
    }


# ---------------------------------------------------------
# 9. SAVE REPORT
# ---------------------------------------------------------

def save_report(report: dict) -> None:
    """Save profiling results as a JSON file."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nReport saved to: {REPORT_PATH}")


# ---------------------------------------------------------
# 10. DISPLAY SUMMARY
# ---------------------------------------------------------

def display_summary(report: dict) -> None:
    """Display important profiling information."""

    basic = report["basic_information"]
    quality = report["data_quality"]
    business = report["business_validation"]

    print("\n" + "=" * 60)
    print("          COLDCHAIN-AI DATA PROFILING REPORT")
    print("=" * 60)

    print("\nDATASET INFORMATION")
    print("-" * 60)
    print("Total records:", basic["total_rows"])
    print("Total columns:", basic["total_columns"])
    print("Memory usage:", basic["memory_usage_mb"], "MB")

    print("\nDATA QUALITY")
    print("-" * 60)
    print("Duplicate rows:", quality["duplicate_rows"])
    print("Missing values:", quality["missing_value_count"])
    print(
        "Columns with missing values:",
        len(quality["columns_with_missing_values"])
    )

    print("\nMISSING REQUIRED COLUMNS")
    print("-" * 60)

    if quality["required_columns_missing"]:
        for column in quality["required_columns_missing"]:
            print("-", column)
    else:
        print("All expected business columns are present.")

    print("\nBUSINESS VALIDATION")
    print("-" * 60)

    for check, result in business.items():
        print(f"{check}: {result}")

    print("\n" + "=" * 60)
    print("DATA PROFILING COMPLETED")
    print("=" * 60)


# ---------------------------------------------------------
# 11. MAIN EXECUTION
# ---------------------------------------------------------

def main():

    try:
        df = load_dataset()

        report = generate_profile(df)

        display_summary(report)

        save_report(report)

    except Exception as error:
        print("\nData profiling failed.")
        print("Reason:", error)
        sys.exit(1)


if __name__ == "__main__":
    main()
