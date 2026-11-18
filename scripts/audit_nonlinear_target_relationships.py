
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT / "data" / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

OUTPUT_DIR = ROOT / "data" / "processed"

df = pd.read_csv(DATA_PATH, low_memory=False)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

targets = [
    "delay_probability",
    "delivery_time_deviation",
    "disruption_likelihood_score",
]

numeric_columns = df.select_dtypes(include="number").columns.tolist()

excluded = set(targets)

features = [
    col for col in numeric_columns
    if col not in excluded
]

relationship_rows = []

print("\n========== NONLINEAR RELATIONSHIP AUDIT ==========")

# --------------------------------------------------
# 1. Quantile-bin analysis
# --------------------------------------------------

for target in targets:

    print(f"\n--- Target: {target} ---")

    target_std = df[target].std()

    for feature in features:

        if df[feature].nunique() < 10:
            continue

        try:
            bins = pd.qcut(
                df[feature],
                q=10,
                duplicates="drop"
            )

            grouped = (
                df.groupby(bins, observed=True)[target]
                .agg(["count", "mean"])
            )

            if len(grouped) < 3:
                continue

            mean_spread = (
                grouped["mean"].max()
                - grouped["mean"].min()
            )

            normalized_spread = (
                mean_spread / target_std
                if target_std > 0 else np.nan
            )

            relationship_rows.append({
                "target": target,
                "feature": feature,
                "number_of_bins": len(grouped),
                "target_mean_spread": mean_spread,
                "normalized_spread": normalized_spread,
                "pearson_correlation": df[feature].corr(
                    df[target], method="pearson"
                ),
                "spearman_correlation": df[feature].corr(
                    df[target], method="spearman"
                ),
            })

        except (ValueError, TypeError):
            continue

# --------------------------------------------------
# 2. Display strongest binned relationships
# --------------------------------------------------

relationships = pd.DataFrame(relationship_rows)

if not relationships.empty:

    for target in targets:

        print(f"\nTop binned relationships: {target}")

        result = (
            relationships[
                relationships["target"] == target
            ]
            .sort_values(
                "normalized_spread",
                ascending=False
            )
            .head(10)
        )

        print(
            result[
                [
                    "feature",
                    "normalized_spread",
                    "pearson_correlation",
                    "spearman_correlation",
                ]
            ].round(4).to_string(index=False)
        )

    relationships.to_csv(
        OUTPUT_DIR / "nonlinear_target_relationships.csv",
        index=False
    )

# --------------------------------------------------
# 3. Temporal diagnostics
# --------------------------------------------------

print("\n--- Temporal diagnostics ---")

temporal_rows = []

df = df.sort_values("timestamp").reset_index(drop=True)

df["year"] = df["timestamp"].dt.year
df["month"] = df["timestamp"].dt.to_period("M").astype(str)

for target in targets:

    series = df[target]

    temporal_rows.append({
        "target": target,
        "correlation_with_time": series.corr(
            pd.Series(np.arange(len(series)))
        ),
        "lag_1_autocorrelation": series.autocorr(lag=1),
        "lag_24_autocorrelation": series.autocorr(lag=24),
        "lag_168_autocorrelation": series.autocorr(lag=168),
    })

    print(f"\n{target}")

    print(
        "Year-wise averages:"
    )

    print(
        df.groupby("year")[target]
        .mean()
        .round(4).to_string()
    )

temporal = pd.DataFrame(temporal_rows)

print("\nAutocorrelation summary:")
print(temporal.round(4).to_string(index=False))

temporal.to_csv(
    OUTPUT_DIR / "target_temporal_diagnostics.csv",
    index=False
)

print("\n========== AUDIT COMPLETED ==========")

print(
    "Generated:\n"
    "- nonlinear_target_relationships.csv\n"
    "- target_temporal_diagnostics.csv"
)

print("Original dataset was not modified.")
