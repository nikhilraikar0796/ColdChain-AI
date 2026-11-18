
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import ExtraTreesRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline


# --------------------------------------------------
# 1. Paths and experiment configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_supply_chain_data.csv"
REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "nonlinear_model_signal_audit.txt"

TARGET = "delivery_time_deviation"

FEATURES = [
    "vehicle_gps_latitude",
    "vehicle_gps_longitude",
    "fuel_consumption_rate",
    "traffic_congestion_level",
    "warehouse_inventory_level",
    "loading_unloading_time",
    "handling_equipment_availability",
    "weather_condition_severity",
    "port_congestion_level",
    "shipping_costs",
    "supplier_reliability_score",
    "lead_time_days",
    "historical_demand",
    "iot_temperature",
    "route_risk_level",
    "customs_clearance_time",
    "driver_behavior_score",
    "fatigue_monitoring_score",
]

TRAIN_RATIO = 0.80
RANDOM_STATE = 42


# --------------------------------------------------
# 2. Load and validate data
# --------------------------------------------------

def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    required_columns = ["timestamp", TARGET] + FEATURES
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing from dataset: {missing_columns}"
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    if df["timestamp"].isna().any():
        raise ValueError("Invalid timestamps found. Resolve them before modelling.")

    df = df.sort_values("timestamp").reset_index(drop=True)

    for column in FEATURES + [TARGET]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=[TARGET]).reset_index(drop=True)

    if len(df) < 10:
        raise ValueError("Insufficient records for the experiment.")

    return df


# --------------------------------------------------
# 3. Chronological train-test split
# --------------------------------------------------

def split_data(df):
    split_index = int(len(df) * TRAIN_RATIO)

    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()

    X_train = train_df[FEATURES]
    X_test = test_df[FEATURES]

    y_train = train_df[TARGET]
    y_test = test_df[TARGET]

    return X_train, X_test, y_train, y_test, train_df, test_df


# --------------------------------------------------
# 4. Evaluation helper
# --------------------------------------------------

def evaluate_model(name, y_true, predictions):
    mae = mean_absolute_error(y_true, predictions)
    rmse = np.sqrt(mean_squared_error(y_true, predictions))
    r2 = r2_score(y_true, predictions)

    return {
        "model": name,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
    }


# --------------------------------------------------
# 5. Main experiment
# --------------------------------------------------

def main():
    print("\n========== NONLINEAR MODEL SIGNAL AUDIT ==========\n")

    df = load_data()

    (
        X_train,
        X_test,
        y_train,
        y_test,
        train_df,
        test_df,
    ) = split_data(df)

    print(f"Total records : {len(df):,}")
    print(f"Training rows : {len(X_train):,}")
    print(f"Testing rows  : {len(X_test):,}")
    print(f"Features      : {len(FEATURES)}")
    print(f"Target        : {TARGET}")

    print("\nChronological split:")
    print(f"Train: {train_df['timestamp'].min()} to "
          f"{train_df['timestamp'].max()}")
    print(f"Test : {test_df['timestamp'].min()} to "
          f"{test_df['timestamp'].max()}")

    # ----------------------------------------------
    # Model 1: Mean prediction baseline
    # ----------------------------------------------

    baseline_predictions = np.full(
        shape=len(y_test),
        fill_value=y_train.mean()
    )

    baseline_result = evaluate_model(
        "Mean baseline",
        y_test,
        baseline_predictions
    )

    # ----------------------------------------------
    # Model 2: Linear regression
    # ----------------------------------------------

    linear_model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", LinearRegression()),
    ])

    linear_model.fit(X_train, y_train)
    linear_predictions = linear_model.predict(X_test)

    linear_result = evaluate_model(
        "Linear regression",
        y_test,
        linear_predictions
    )

    # ----------------------------------------------
    # Model 3: Extra Trees regression
    # ----------------------------------------------

    extra_trees_model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        (
            "model",
            ExtraTreesRegressor(
                n_estimators=300,
                min_samples_leaf=5,
                max_features=1.0,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
    ])

    extra_trees_model.fit(X_train, y_train)
    extra_trees_predictions = extra_trees_model.predict(X_test)

    extra_trees_result = evaluate_model(
        "ExtraTrees regression",
        y_test,
        extra_trees_predictions
    )

    # ----------------------------------------------
    # Results
    # ----------------------------------------------

    results = [
        baseline_result,
        linear_result,
        extra_trees_result,
    ]

    results_df = pd.DataFrame(results)

    baseline_mae = baseline_result["mae"]
    baseline_rmse = baseline_result["rmse"]

    mae_improvement = (
        (baseline_mae - extra_trees_result["mae"])
        / baseline_mae
    ) * 100

    rmse_improvement = (
        (baseline_rmse - extra_trees_result["rmse"])
        / baseline_rmse
    ) * 100

    print("\n========== MODEL COMPARISON ==========\n")
    print(
        results_df.to_string(
            index=False,
            formatters={
                "mae": "{:.6f}".format,
                "rmse": "{:.6f}".format,
                "r2": "{:.6f}".format,
            },
        )
    )

    print("\n========== EXTRA TREES VS BASELINE ==========\n")
    print(f"MAE improvement : {mae_improvement:.4f}%")
    print(f"RMSE improvement: {rmse_improvement:.4f}%")

    # ----------------------------------------------
    # Feature importance (exploratory)
    # ----------------------------------------------

    fitted_model = extra_trees_model.named_steps["model"]

    importance_df = pd.DataFrame({
        "feature": FEATURES,
        "importance": fitted_model.feature_importances_,
    }).sort_values(
        "importance",
        ascending=False
    )

    print("\n========== TOP 10 FEATURE IMPORTANCES ==========\n")
    print(
        importance_df.head(10).to_string(
            index=False,
            formatters={"importance": "{:.6f}".format}
        )
    )

    # ----------------------------------------------
    # Save report
    # ----------------------------------------------

    report_lines = [
        "NONLINEAR MODEL SIGNAL AUDIT",
        "=" * 60,
        f"Target: {TARGET}",
        f"Total records: {len(df)}",
        f"Training rows: {len(X_train)}",
        f"Testing rows: {len(X_test)}",
        f"Number of features: {len(FEATURES)}",
        f"Training period: {train_df['timestamp'].min()} to "
        f"{train_df['timestamp'].max()}",
        f"Testing period: {test_df['timestamp'].min()} to "
        f"{test_df['timestamp'].max()}",
        "",
        "FEATURES",
        "-" * 60,
        *FEATURES,
        "",
        "MODEL COMPARISON",
        "-" * 60,
        results_df.to_string(index=False),
        "",
        f"ExtraTrees MAE improvement vs baseline: {mae_improvement:.4f}%",
        f"ExtraTrees RMSE improvement vs baseline: {rmse_improvement:.4f}%",
        "",
        "TOP 10 EXTRA TREES FEATURE IMPORTANCES",
        "-" * 60,
        importance_df.head(10).to_string(index=False),
        "",
        "IMPORTANT CAVEATS",
        "-" * 60,
        "This is a diagnostic experiment, not a production model.",
        "No hyperparameter tuning was performed.",
        "Feature importance does not establish causation.",
        "Weak performance does not prove that the dataset is synthetic.",
        "Dataset provenance, target-generation methodology and entity "
        "semantics remain unverified.",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(report_lines),
        encoding="utf-8"
    )

    print(f"\nReport saved to:\n{REPORT_PATH}")
    print("\n========== AUDIT COMPLETED ==========\n")


if __name__ == "__main__":
    main()
