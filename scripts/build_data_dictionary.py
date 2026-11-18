
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = ROOT / "data/raw/dynamic_supply_chain_logistics_dataset.csv"
OUTPUT_PATH = ROOT / "data/processed/data_dictionary.csv"

df = pd.read_csv(DATA_PATH, low_memory=False)

# Candidate definitions are deliberately marked provisional.
# They must be checked against the original dataset documentation.

definitions = {
    "timestamp": (
        "Date and time associated with the observation.",
        "Datetime",
        "Timestamp",
        "Valid and parseable datetime",
        "Observation time; not automatically a shipment ID"
    ),
    "vehicle_gps_latitude": (
        "Latitude of the recorded vehicle location.",
        "Degrees",
        "-90 to 90",
        "Must be between -90 and 90",
        "Potential geographic feature"
    ),
    "vehicle_gps_longitude": (
        "Longitude of the recorded vehicle location.",
        "Degrees",
        "-180 to 180",
        "Must be between -180 and 180",
        "Potential geographic feature"
    ),
    "fuel_consumption_rate": (
        "Vehicle fuel consumption measurement or rate.",
        "Unverified",
        "Observed dataset range",
        "Must be finite; physical limits require verification",
        "Potential feature; unit and meaning unverified"
    ),
    "eta_variation_hours": (
        "Variation in estimated arrival time.",
        "Hours (candidate; verify)",
        "Observed dataset range",
        "Must be finite; negative values require semantic verification",
        "Potential feature; timing semantics unverified"
    ),
    "traffic_congestion_level": (
        "Numerical traffic congestion indicator.",
        "Unverified",
        "Observed dataset range",
        "Finite value; scale requires verification",
        "Potential feature"
    ),
    "warehouse_inventory_level": (
        "Numerical warehouse inventory measurement.",
        "Unverified",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature"
    ),
    "loading_unloading_time": (
        "Time associated with loading and unloading operations.",
        "Unverified",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature; unit requires verification"
    ),
    "handling_equipment_availability": (
        "Numerical indicator of handling equipment availability.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; score direction requires verification"
    ),
    "order_fulfillment_status": (
        "Numerical order fulfillment indicator or score.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; meaning and score direction unverified"
    ),
    "weather_condition_severity": (
        "Numerical indicator of weather severity.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; scale requires verification"
    ),
    "port_congestion_level": (
        "Numerical port congestion indicator.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 10",
        "Potential feature; port identity is unavailable"
    ),
    "shipping_costs": (
        "Recorded shipping cost measurement.",
        "Currency unverified",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature; currency and cost basis unverified"
    ),
    "supplier_reliability_score": (
        "Numerical supplier reliability score.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; score direction requires verification"
    ),
    "lead_time_days": (
        "Recorded or estimated supply-chain lead time.",
        "Days (candidate; verify)",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature; definition requires verification"
    ),
    "historical_demand": (
        "Numerical historical demand measurement.",
        "Unverified",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature; aggregation period requires verification"
    ),
    "iot_temperature": (
        "Temperature measurement from an IoT source.",
        "°C indicated by local SOP; dataset unit requires verification",
        "Observed dataset range",
        "Must be finite; cargo-specific limits require verification",
        "Potential feature; cold-chain applicability conditional"
    ),
    "cargo_condition_status": (
        "Numerical cargo condition indicator or score.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; score direction requires verification"
    ),
    "route_risk_level": (
        "Numerical indicator of route-related risk.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 10",
        "Potential feature; scale requires verification"
    ),
    "customs_clearance_time": (
        "Time associated with customs clearance.",
        "Unverified",
        "Observed dataset range",
        "Must be finite and non-negative",
        "Potential feature; unit requires verification"
    ),
    "driver_behavior_score": (
        "Numerical indicator of driver behavior.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; score direction requires verification"
    ),
    "fatigue_monitoring_score": (
        "Numerical fatigue monitoring indicator.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential feature; score direction requires verification"
    ),
    "disruption_likelihood_score": (
        "Numerical indicator of disruption likelihood.",
        "Unverified",
        "Observed dataset range",
        "Observed values are between 0 and 1",
        "Potential predictor or outcome; provenance requires verification"
    ),
    "delay_probability": (
        "Numerical probability-like indicator of shipment delay.",
        "Probability scale (candidate)",
        "0 to 1",
        "Must be between 0 and 1",
        "Potential ML target; target provenance and calculation require verification"
    ),
    "risk_classification": (
        "Categorical operational risk classification.",
        "Category",
        "Low Risk, Moderate Risk, High Risk",
        "Must belong to the documented category set",
        "Potential classification target; derivation requires verification"
    ),
    "delivery_time_deviation": (
        "Numerical deviation associated with delivery time.",
        "Unverified",
        "Observed dataset range",
        "Must be finite; negative values require semantic verification",
        "Potential outcome; definition and unit require verification"
    ),
}

records = []

for column in df.columns:
    series = df[column]

    definition, unit, expected_range, validation, ml_role = definitions[column]

    if pd.api.types.is_numeric_dtype(series):
        observed_min = series.min()
        observed_max = series.max()
    else:
        observed_min = None
        observed_max = None

    records.append({
        "column_name": column,
        "data_type": str(series.dtype),
        "non_null_count": int(series.notna().sum()),
        "missing_count": int(series.isna().sum()),
        "unique_values": int(series.nunique()),
        "observed_min": observed_min,
        "observed_max": observed_max,
        "candidate_business_definition": definition,
        "unit": unit,
        "expected_range_or_categories": expected_range,
        "proposed_validation_rule": validation,
        "definition_status": "PROVISIONAL - VERIFY",
        "potential_ml_role": ml_role,
    })

dictionary = pd.DataFrame(records)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
dictionary.to_csv(OUTPUT_PATH, index=False)

print("\n========== DATA DICTIONARY GENERATED ==========")
print("Total columns documented:", len(dictionary))
print("Provisional definitions:", len(dictionary))

print("\nColumn names:")
for column in dictionary["column_name"]:
    print("-", column)

print("\nOutput file:")
print(OUTPUT_PATH)

print("\nOriginal dataset was not modified.")
