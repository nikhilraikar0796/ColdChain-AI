
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

df = pd.read_csv(DATA_PATH, low_memory=False)

# Convert timestamps
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

timestamps = df["timestamp"]

print("\n========== TIMESTAMP VALIDATION ==========")

# 1. Invalid timestamps
print("Invalid timestamps:", timestamps.isna().sum())

valid = timestamps.dropna()

# 2. Date range
print("First timestamp:", valid.min())
print("Last timestamp:", valid.max())

# 3. Duplicate timestamps
print("Duplicate timestamps:", valid.duplicated().sum())

# 4. Check chronological ordering
print(
    "Already sorted:",
    valid.is_monotonic_increasing
)

# 5. Check time interval distribution
sorted_times = valid.sort_values()

intervals = sorted_times.diff().dropna()

print("\nTime interval distribution:")
print(intervals.value_counts().head(10).to_string())

# 6. Check missing hourly timestamps
unique_times = pd.DatetimeIndex(valid.unique()).sort_values()

expected_times = pd.date_range(
    start=unique_times.min(),
    end=unique_times.max(),
    freq="h"
)

missing_times = expected_times.difference(unique_times)

print("\n========== HOURLY CONTINUITY ==========")
print("Expected hourly records:", len(expected_times))
print("Actual unique timestamps:", len(unique_times))
print("Missing hourly timestamps:", len(missing_times))

if len(missing_times) > 0:
    print("\nFirst 10 missing timestamps:")
    print(missing_times[:10].to_list())

print("\nTimestamp validation completed.")
