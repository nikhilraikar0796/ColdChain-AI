
from pathlib import Path

import numpy as np
import pandas as pd


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
    / "multivariate_signal_audit.txt"
)

TARGET = "delivery_time_deviation"

TEST_FRACTION = 0.20

# Exclude target, alternative targets, status fields,
# and features with unresolved leakage/meaning concerns.
EXCLUDED_COLUMNS = {
    "timestamp",
    "delivery_time_deviation",
    "eta_variation_hours",
    "delay_probability",
    "disruption_likelihood_score",
    "risk_classification",
    "order_fulfillment_status",
    "cargo_condition_status",
    "telemetry_id",
}


# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------

def calculate_metrics(actual, predicted):

    errors = actual - predicted

    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))

    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)

    r2 = 1 - (ss_res / ss_tot)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    if TARGET not in df.columns:
        raise ValueError(f"Target not found: {TARGET}")

    if "timestamp" not in df.columns:
        raise ValueError("Timestamp column is missing.")

    # -----------------------------------------------------
    # 1. PREPARE DATA
    # -----------------------------------------------------

    print("=" * 70)
    print("PHASE 2 - MULTIVARIATE PREDICTIVE SIGNAL AUDIT")
    print("=" * 70)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df[TARGET] = pd.to_numeric(
        df[TARGET],
        errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", TARGET]
    ).sort_values("timestamp").reset_index(drop=True)

    # Only operational numeric features.
    feature_columns = [
        col
        for col in df.select_dtypes(include=np.number).columns
        if col not in EXCLUDED_COLUMNS
    ]

    if not feature_columns:
        raise ValueError("No eligible operational features found.")

    X = df[feature_columns].copy()
    y = df[TARGET].copy()

    # Replace infinities and impute missing values
    # using training data only.
    X = X.replace([np.inf, -np.inf], np.nan)

    # -----------------------------------------------------
    # 2. CHRONOLOGICAL SPLIT
    # -----------------------------------------------------

    split_index = int(len(df) * (1 - TEST_FRACTION))

    X_train = X.iloc[:split_index].copy()
    X_test = X.iloc[split_index:].copy()

    y_train = y.iloc[:split_index].to_numpy(dtype=float)
    y_test = y.iloc[split_index:].to_numpy(dtype=float)

    train_medians = X_train.median()

    X_train = X_train.fillna(train_medians)
    X_test = X_test.fillna(train_medians)

    # Remove columns with no variation in training data.
    valid_columns = [
        col
        for col in X_train.columns
        if X_train[col].nunique() > 1
    ]

    X_train = X_train[valid_columns]
    X_test = X_test[valid_columns]

    # -----------------------------------------------------
    # 3. STANDARDIZE USING TRAINING STATISTICS
    # -----------------------------------------------------

    means = X_train.mean()
    stds = X_train.std(ddof=0)

    valid_std_columns = stds[stds > 1e-12].index.tolist()

    X_train = X_train[valid_std_columns]
    X_test = X_test[valid_std_columns]

    means = X_train.mean()
    stds = X_train.std(ddof=0)

    X_train_scaled = (
        X_train - means
    ) / stds

    X_test_scaled = (
        X_test - means
    ) / stds

    train_matrix = np.column_stack([
        np.ones(len(X_train_scaled)),
        X_train_scaled.to_numpy(dtype=float),
    ])

    test_matrix = np.column_stack([
        np.ones(len(X_test_scaled)),
        X_test_scaled.to_numpy(dtype=float),
    ])

    # -----------------------------------------------------
    # 4. BASELINE MODEL
    # -----------------------------------------------------

    baseline_prediction = np.full(
        len(y_test),
        np.mean(y_train)
    )

    baseline_metrics = calculate_metrics(
        y_test,
        baseline_prediction
    )

    # -----------------------------------------------------
    # 5. MULTIVARIATE LINEAR REGRESSION
    # -----------------------------------------------------

    coefficients, _, _, _ = np.linalg.lstsq(
        train_matrix,
        y_train,
        rcond=None
    )

    predictions = test_matrix @ coefficients

    model_metrics = calculate_metrics(
        y_test,
        predictions
    )

    # -----------------------------------------------------
    # 6. RESULTS
    # -----------------------------------------------------

    report = []

    def log(message=""):
        message = str(message)
        print(message)
        report.append(message)

    log("=" * 70)
    log("MULTIVARIATE PREDICTIVE SIGNAL RESULTS")
    log("=" * 70)

    log(f"Total observations : {len(df):,}")
    log(f"Training rows      : {len(X_train):,}")
    log(f"Testing rows       : {len(X_test):,}")
    log(f"Features used      : {len(valid_std_columns)}")

    log("\nFeatures:")
    for feature in valid_std_columns:
        log(f"- {feature}")

    log("\nTraining period:")
    log(
        f"{df['timestamp'].iloc[0]} to "
        f"{df['timestamp'].iloc[split_index - 1]}"
    )

    log("\nTesting period:")
    log(
        f"{df['timestamp'].iloc[split_index]} to "
        f"{df['timestamp'].iloc[-1]}"
    )

    log("\nBASELINE - TRAINING MEAN PREDICTION")
    for metric, value in baseline_metrics.items():
        log(f"{metric}: {value:.6f}")

    log("\nMULTIVARIATE LINEAR REGRESSION")
    for metric, value in model_metrics.items():
        log(f"{metric}: {value:.6f}")

    log("\nMODEL IMPROVEMENT OVER BASELINE")

    mae_improvement = (
        (baseline_metrics["MAE"] - model_metrics["MAE"])
        / baseline_metrics["MAE"]
        * 100
    )

    rmse_improvement = (
        (baseline_metrics["RMSE"] - model_metrics["RMSE"])
        / baseline_metrics["RMSE"]
        * 100
    )

    log(f"MAE improvement : {mae_improvement:.2f}%")
    log(f"RMSE improvement: {rmse_improvement:.2f}%")

    log("\nINTERPRETATION")

    if model_metrics["R2"] <= 0:
        log(
            "The model does not outperform the test-set "
            "mean baseline in terms of squared error."
        )
    elif model_metrics["R2"] < 0.10:
        log(
            "The model explains very little test-set variation. "
            "Predictive signal appears weak."
        )
    else:
        log(
            "The model captures some test-set variation. "
            "Further validation is required."
        )

    log(
        "\nIMPORTANT: This is a linear baseline diagnostic, "
        "not proof that nonlinear models will fail."
    )

    log(
        "The chronological split assumes the timestamp ordering "
        "represents a meaningful prediction timeline."
    )

    log(
        "No shipment identifiers are available, so independent "
        "shipment-level validation cannot be performed."
    )

    # -----------------------------------------------------
    # 7. SAVE REPORT
    # -----------------------------------------------------

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_PATH.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print(f"\nReport saved: {REPORT_PATH}")
    print("\nMULTIVARIATE SIGNAL AUDIT COMPLETED")


if __name__ == "__main__":
    main()
