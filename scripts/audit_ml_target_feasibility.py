
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    ROOT
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "processed"
    / "ml_target_feasibility_report.txt"
)

df = pd.read_csv(DATA_PATH, low_memory=False)

print("\n========== ML TARGET FEASIBILITY AUDIT ==========")

# --------------------------------------------------
# 1. Candidate target distributions
# --------------------------------------------------

candidate_targets = [
    "delay_probability",
    "risk_classification",
    "delivery_time_deviation",
    "disruption_likelihood_score",
]

print("\n--- Candidate target distributions ---")

for column in candidate_targets:
    print(f"\n{column}")

    if df[column].dtype == "object" or isinstance(
        df[column].dtype, pd.StringDtype
    ):
        print(df[column].value_counts().to_string())
    else:
        print(df[column].describe().round(4).to_string())

# --------------------------------------------------
# 2. Risk classification vs delay probability
# --------------------------------------------------

print("\n--- Risk classification vs delay probability ---")

risk_analysis = (
    df.groupby("risk_classification")["delay_probability"]
    .agg(["count", "mean", "median", "std"])
    .round(4)
)

print(risk_analysis.to_string())

# --------------------------------------------------
# 3. Delay probability distribution by risk category
# --------------------------------------------------

print("\n--- Delay probability bins by risk category ---")

df["delay_probability_bin"] = pd.cut(
    df["delay_probability"],
    bins=[-0.001, 0.25, 0.50, 0.75, 1.001],
    labels=["0-0.25", "0.25-0.50", "0.50-0.75", "0.75-1.00"]
)

cross_tab = pd.crosstab(
    df["risk_classification"],
    df["delay_probability_bin"],
    normalize="index"
).round(3)

print(cross_tab.to_string())

# --------------------------------------------------
# 4. Correlation with candidate numerical targets
# --------------------------------------------------

numeric_df = df.select_dtypes(include="number")

candidate_numeric = [
    "delay_probability",
    "delivery_time_deviation",
    "disruption_likelihood_score",
]

for target in candidate_numeric:
    print(f"\n--- Pearson correlations with {target} ---")

    correlations = (
        numeric_df.corr(method="pearson")[target]
        .drop(target)
        .sort_values(key=abs, ascending=False)
    )

    print(correlations.head(12).round(4).to_string())

    print(f"\n--- Spearman correlations with {target} ---")

    rank_correlations = (
        numeric_df.corr(method="spearman")[target]
        .drop(target)
        .sort_values(key=abs, ascending=False)
    )

    print(rank_correlations.head(12).round(4).to_string())

# --------------------------------------------------
# 5. Relationship between possible outcomes
# --------------------------------------------------

print("\n--- Candidate outcome relationships ---")

outcome_correlations = df[
    [
        "delay_probability",
        "delivery_time_deviation",
        "disruption_likelihood_score",
    ]
].corr(method="pearson")

print(outcome_correlations.round(4).to_string())

# --------------------------------------------------
# 6. Check exact duplicate numerical values
# --------------------------------------------------

print("\n--- Candidate target uniqueness ---")

for column in candidate_numeric:
    print(
        f"{column}: "
        f"{df[column].nunique()} unique values"
    )

# --------------------------------------------------
# 7. Save report
# --------------------------------------------------

with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    file.write("ML TARGET FEASIBILITY AUDIT\n\n")
    file.write(f"Records: {len(df)}\n")
    file.write(f"Columns: {len(df.columns)}\n\n")

    file.write("RISK ANALYSIS\n")
    file.write(risk_analysis.to_string())

    file.write("\n\nRISK VS DELAY PROBABILITY\n")
    file.write(cross_tab.to_string())

    file.write("\n\nOUTCOME CORRELATIONS\n")
    file.write(outcome_correlations.to_string())

print("\nReport saved:")
print(OUTPUT_PATH)

print("\nML target feasibility audit completed.")
print("No source data was modified.")
