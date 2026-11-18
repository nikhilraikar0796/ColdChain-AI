
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

latitude = df["vehicle_gps_latitude"]
longitude = df["vehicle_gps_longitude"]

print("\n========== GEOGRAPHIC DATA INVESTIGATION ==========")

# 1. Coordinate statistics
print("\n--- Latitude statistics ---")
print(latitude.describe().round(3).to_string())

print("\n--- Longitude statistics ---")
print(longitude.describe().round(3).to_string())

# 2. Approximate Southern California screening region
# These are broad investigation bounds, not official boundaries.
southern_california = (
    latitude.between(32.5, 35.5)
    & longitude.between(-120.5, -114.0)
)

# 3. Approximate continental US screening region
continental_us = (
    latitude.between(24.0, 50.0)
    & longitude.between(-125.0, -66.0)
)

print("\n--- Geographic screening ---")

print(
    "Records in approximate Southern California region:",
    int(southern_california.sum())
)

print(
    "Percentage in approximate Southern California region:",
    round(southern_california.mean() * 100, 2),
    "%"
)

print(
    "Records in approximate continental US bounds:",
    int(continental_us.sum())
)

print(
    "Records outside approximate continental US bounds:",
    int((~continental_us).sum())
)

# 4. Coordinate uniqueness
print("\n--- Coordinate uniqueness ---")

unique_locations = df[
    ["vehicle_gps_latitude", "vehicle_gps_longitude"]
].drop_duplicates()

print("Total records:", len(df))
print("Unique coordinate pairs:", len(unique_locations))
print(
    "Repeated coordinate pairs:",
    len(df) - len(unique_locations)
)

# 5. Geographic concentration by latitude/longitude bands
print("\n--- Latitude bands ---")

latitude_bins = pd.cut(
    latitude,
    bins=[-90, 30, 35, 40, 45, 50, 90]
)

print(latitude_bins.value_counts().sort_index().to_string())

print("\n--- Longitude bands ---")

longitude_bins = pd.cut(
    longitude,
    bins=[-180, -120, -110, -100, -90, -80, -70, 180]
)

print(longitude_bins.value_counts().sort_index().to_string())

print("\nGeographic investigation completed.")
