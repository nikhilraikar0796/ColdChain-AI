
from pathlib import Path

import pandas as pd

# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "data_dictionary_draft.csv"
)

# --------------------------------------------------
# Load dataset
# --------------------------------------------------

df = pd.read_csv(DATA_PATH, low_memory=False)

print("\n========== DATASET OVERVIEW ==========")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

# --------------------------------------------------
# Generate draft data dictionary
# --------------------------------------------------

dictionary = []

for column in df.columns:
    series = df[column]

    record = {
        "column_name": column,
        "data_type": str(series.dtype),
        "non_null_count": int(series.notna().sum()),
        "missing_count": int(series.isna().sum()),
        "unique_values": int(series.nunique()),
        "sample_values": " | ".join(
            series.dropna().astype(str).unique()[:3]
        ),
        "business_definition": "TO BE VERIFIED",
        "unit": "TO BE VERIFIED",
        "validation_rule": "TO BE DEFINED",
    }

    if pd.api.types.is_numeric_dtype(series):
        record.update({
            "minimum": series.min(),
            "maximum": series.max(),
            "mean": round(series.mean(), 3),
        })
    else:
        record.update({
            "minimum": None,
            "maximum": None,
            "mean": None,
        })

    dictionary.append(record)

dictionary_df = pd.DataFrame(dictionary)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
dictionary_df.to_csv(OUTPUT_PATH, index=False)

print("\n========== COLUMN METADATA ==========")

print(
    dictionary_df[
        [
            "column_name",
            "data_type",
            "unique_values",
            "missing_count",
        ]
    ].to_string(index=False)
)

# --------------------------------------------------
# Risk classification distribution
# --------------------------------------------------

print("\n========== RISK DISTRIBUTION ==========")

risk_distribution = (
    df["risk_classification"]
    .value_counts(dropna=False)
    .to_frame("count")
)

risk_distribution["percentage"] = (
    risk_distribution["count"] / len(df) * 100
).round(2)

print(risk_distribution.to_string())

# --------------------------------------------------
# Timestamp distribution
# --------------------------------------------------

print("\n========== YEAR-WISE RECORD DISTRIBUTION ==========")

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

print(
    df["timestamp"]
    .dt.year
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nDraft data dictionary created:")
print(OUTPUT_PATH)
