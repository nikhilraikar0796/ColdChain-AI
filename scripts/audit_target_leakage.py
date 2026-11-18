
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "dynamic_supply_chain_logistics_dataset.csv"
)

REPORT_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "target_leakage_audit.txt"
)

TARGET = "delivery_time_deviation"
POTENTIAL_LEAK = "eta_variation_hours"
OTHER_TARGET = "order_fulfillment_status"


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def correlation_report(x, y, label):
    pearson = pearsonr(x, y)
    spearman = spearmanr(x, y)

    print(f"\n{label}")
    print(f"Pearson correlation : {pearson.statistic:.6f}")
    print(f"Pearson p-value     : {pearson.pvalue:.6g}")
    print(f"Spearman correlation: {spearman.statistic:.6f}")
    print(f"Spearman p-value    : {spearman.pvalue:.6g}")


# ---------------------------------------------------------
# MAIN AUDIT
# ---------------------------------------------------------

def main():

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required = [TARGET, POTENTIAL_LEAK, OTHER_TARGET]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df[POTENTIAL_LEAK] = pd.to_numeric(
        df[POTENTIAL_LEAK], errors="coerce"
    )

    audit = df[[TARGET, POTENTIAL_LEAK]].dropna().copy()

    y = audit[TARGET]
    x = audit[POTENTIAL_LEAK]

    output = []

    def log(message=""):
        message = str(message)
        print(message)
        output.append(message)

    log("=" * 70)
    log("PHASE 2 - TARGET LEAKAGE AUDIT")
    log("=" * 70)
    log(f"Dataset rows             : {len(df):,}")
    log(f"Valid comparison rows    : {len(audit):,}")
    log(f"Candidate target         : {TARGET}")
    log(f"Potential leakage feature: {POTENTIAL_LEAK}")

    # -----------------------------------------------------
    # 1. DESCRIPTIVE STATISTICS
    # -----------------------------------------------------

    log("\n1. DESCRIPTIVE STATISTICS")

    for column in [TARGET, POTENTIAL_LEAK]:
        log(f"\n{column}")
        log(df[column].describe().round(4).to_string())
        log(f"Unique values: {df[column].nunique():,}")

    # -----------------------------------------------------
    # 2. CORRELATION
    # -----------------------------------------------------

    log("\n2. TARGET VS POTENTIAL LEAKAGE FEATURE")

    correlation_report(x, y, "ETA variation vs delivery deviation")

    pearson_value = pearsonr(x, y).statistic
    spearman_value = spearmanr(x, y).statistic

    # -----------------------------------------------------
    # 3. DIRECT COMPARISON
    # -----------------------------------------------------

    log("\n3. DIRECT VALUE COMPARISON")

    difference = y - x
    absolute_difference = difference.abs()

    exact_matches = np.isclose(y, x, atol=1e-8).sum()
    rounded_matches = np.isclose(y.round(2), x.round(2)).sum()

    log(f"Exact matches              : {exact_matches:,}")
    log(f"Exact match percentage     : {exact_matches / len(audit) * 100:.2f}%")
    log(f"Matches after rounding 2dp : {rounded_matches:,}")
    log(f"Rounded match percentage   : {rounded_matches / len(audit) * 100:.2f}%")

    log("\nDifference (target - ETA variation):")
    log(difference.describe().round(4).to_string())

    log("\nAbsolute difference:")
    log(absolute_difference.describe().round(4).to_string())

    # -----------------------------------------------------
    # 4. LINEAR RELATIONSHIP
    # -----------------------------------------------------

    log("\n4. LINEAR REGRESSION DIAGNOSTIC")

    slope, intercept = np.polyfit(x, y, 1)
    predictions = slope * x + intercept

    ss_res = np.sum((y - predictions) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)

    r2 = 1 - (ss_res / ss_tot)

    log(f"Intercept  : {intercept:.6f}")
    log(f"Coefficient: {slope:.6f}")
    log(f"R-squared  : {r2:.6f}")

    # -----------------------------------------------------
    # 5. TARGET RELATIONSHIP WITHOUT ETA FEATURE
    # -----------------------------------------------------

    log("\n5. OTHER FEATURE RELATIONSHIPS")
    log("ETA variation is excluded from this analysis.")

    excluded_columns = {
        "delivery_time_deviation",
        "eta_variation_hours",
        "delay_probability",
        "disruption_likelihood_score",
        "risk_classification",
        "order_fulfillment_status",
        "cargo_condition_status",
        "telemetry_id",
    }

    feature_columns = [
        column
        for column in df.select_dtypes(include=np.number).columns
        if column not in excluded_columns
    ]

    results = []

    for column in feature_columns:
        pair = df[[column, TARGET]].dropna()

        if len(pair) < 3 or pair[column].nunique() < 2:
            continue

        pearson = pearsonr(pair[column], pair[TARGET]).statistic
        spearman = spearmanr(pair[column], pair[TARGET]).statistic

        results.append({
            "feature": column,
            "pearson": pearson,
            "spearman": spearman,
            "abs_pearson": abs(pearson),
            "abs_spearman": abs(spearman),
            "rows": len(pair),
        })

    results_df = pd.DataFrame(results)

    if not results_df.empty:
        results_df = results_df.sort_values(
            "abs_spearman", ascending=False
        )

        log("\nFeature relationships ranked by absolute Spearman correlation:")
        log(
            results_df[
                ["feature", "pearson", "spearman", "rows"]
            ].round(5).to_string(index=False)
        )

        results_path = (
            BASE_DIR
            / "data"
            / "processed"
            / "target_feature_correlations_without_eta.csv"
        )

        results_df.to_csv(results_path, index=False)
        log(f"\nFeature correlation CSV saved: {results_path}")

    # -----------------------------------------------------
    # 6. ORDER FULFILLMENT STATUS VALIDATION
    # -----------------------------------------------------

    log("\n6. ORDER FULFILLMENT STATUS VALIDATION")

    fulfillment = pd.to_numeric(
        df[OTHER_TARGET], errors="coerce"
    ).dropna()

    unique_count = fulfillment.nunique()
    binary_values = set(fulfillment.unique()).issubset({0, 1})

    log(f"Unique values: {unique_count:,}")
    log(f"Is binary 0/1: {binary_values}")
    log(f"Minimum      : {fulfillment.min():.6f}")
    log(f"Maximum      : {fulfillment.max():.6f}")

    log("\nSample unique values:")
    log(str(sorted(fulfillment.unique())[:20]))

    # -----------------------------------------------------
    # 7. PRELIMINARY INTERPRETATION
    # -----------------------------------------------------

    log("\n7. PRELIMINARY INTERPRETATION")

    if abs(pearson_value) >= 0.90 or abs(spearman_value) >= 0.90:
        log(
            "WARNING: Very strong association detected. "
            "Investigate potential target leakage or shared calculation."
        )
    elif abs(pearson_value) >= 0.70 or abs(spearman_value) >= 0.70:
        log(
            "CAUTION: Strong association detected. "
            "Investigate the business definitions before using ETA variation."
        )
    else:
        log(
            "No strong direct association detected. "
            "This does not prove that ETA variation is safe to use."
        )

    if not binary_values:
        log(
            "WARNING: order_fulfillment_status is not binary 0/1 "
            "in the observed dataset, contradicting its published description."
        )

    log(
        "\nIMPORTANT: Correlation alone cannot establish leakage. "
        "The data-generation formula and real-world event timing must be verified."
    )

    # -----------------------------------------------------
    # 8. SAVE REPORT
    # -----------------------------------------------------

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(output), encoding="utf-8")

    print(f"\nReport saved: {REPORT_PATH}")
    print("\nTARGET LEAKAGE AUDIT COMPLETED")


if __name__ == "__main__":
    main()
