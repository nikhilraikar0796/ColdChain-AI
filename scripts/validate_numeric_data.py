
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

df = pd.read_csv(DATA_PATH, low_memory=False)

print("\n========== NUMERIC DATA VALIDATION ==========")

# Identify numeric columns
numeric_columns = df.select_dtypes(include="number").columns

# 1. Check infinite values
print("\n--- Infinite values ---")

for column in numeric_columns:
    count = np.isinf(df[column]).sum()

    if count > 0:
        print(f"{column}: {count}")

# 2. Validate GPS coordinates
print("\n--- GPS coordinate validation ---")

invalid_latitude = (
    ~df["vehicle_gps_latitude"].between(-90, 90)
)

invalid_longitude = (
    ~df["vehicle_gps_longitude"].between(-180, 180)
)

print("Invalid latitude:", invalid_latitude.sum())
print("Invalid longitude:", invalid_longitude.sum())

# 3. Validate probability
print("\n--- Delay probability validation ---")

invalid_probability = (
    ~df["delay_probability"].between(0, 1)
)

print("Values outside [0, 1]:", invalid_probability.sum())

# 4. Investigate numeric distributions
print("\n--- Numeric column statistics ---")

statistics = df[numeric_columns].describe(
    percentiles=[0.01, 0.25, 0.50, 0.75, 0.99]
).T

print(
    statistics[
        ["min", "1%", "25%", "50%", "75%", "99%", "max"]
    ].round(3).to_string()
)

# 5. Investigate operational score columns
score_columns = [
    "order_fulfillment_status",
    "cargo_condition_status",
    "supplier_reliability_score",
    "driver_behavior_score",
    "fatigue_monitoring_score",
    "disruption_likelihood_score",
]

print("\n--- Score columns outside [0, 1] ---")

for column in score_columns:
    invalid = ~df[column].between(0, 1)

    print(f"{column}: {invalid.sum()}")

# 6. Save validation summary
summary = {
    "total_records": len(df),
    "invalid_latitude": int(invalid_latitude.sum()),
    "invalid_longitude": int(invalid_longitude.sum()),
    "invalid_delay_probability": int(invalid_probability.sum()),
    "infinite_numeric_values": int(
        np.isinf(df[numeric_columns]).sum().sum()
    ),
}

output_path = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "numeric_validation_summary.csv"
)

pd.DataFrame([summary]).to_csv(output_path, index=False)

print("\nValidation summary saved to:")
print(output_path)
print("\nNumeric validation completed.")
