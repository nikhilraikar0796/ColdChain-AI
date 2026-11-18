
from pathlib import Path

import pandas as pd

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
    / "business_rule_validation_matrix.csv"
)

df = pd.read_csv(DATA_PATH, low_memory=False)

total = len(df)

# Evaluate the four SOP conditions
temperature_breach = df["iot_temperature"] > 4

temperature_eta_breach = (
    temperature_breach
    & (df["eta_variation_hours"] > 1)
)

port_congestion_breach = df["port_congestion_level"] > 7

tier2_escalation = (
    (df["risk_classification"] == "High Risk")
    & (df["delay_probability"] > 0.65)
)

# Document each rule and its limitations
rules = [
    {
        "rule_id": "SOP-01",
        "rule_name": "Cold-chain temperature breach",
        "condition": "iot_temperature > 4.0",
        "matching_records": int(temperature_breach.sum()),
        "percentage": round(temperature_breach.mean() * 100, 2),
        "required_fields": "iot_temperature, cargo_type",
        "status": "CONDITIONAL",
        "limitation": "Cargo category is missing; fresh-perishable applicability is unverified."
    },
    {
        "rule_id": "SOP-02",
        "rule_name": "Emergency cold-storage diversion candidate",
        "condition": "iot_temperature > 4.0 AND eta_variation_hours > 1",
        "matching_records": int(temperature_eta_breach.sum()),
        "percentage": round(temperature_eta_breach.mean() * 100, 2),
        "required_fields": "iot_temperature, cargo_type, eta_variation_hours",
        "status": "CONDITIONAL",
        "limitation": "Cargo category and ETA field semantics require verification."
    },
    {
        "rule_id": "SOP-03",
        "rule_name": "Port congestion diversion",
        "condition": "port_congestion_level > 7.0",
        "matching_records": int(port_congestion_breach.sum()),
        "percentage": round(port_congestion_breach.mean() * 100, 2),
        "required_fields": "port_congestion_level, port_name",
        "status": "NOT FULLY VERIFIABLE",
        "limitation": "Port identity is missing; LA/Long Beach applicability cannot be established."
    },
    {
        "rule_id": "SOP-04",
        "rule_name": "Tier 2 logistics escalation",
        "condition": "risk_classification == 'High Risk' AND delay_probability > 0.65",
        "matching_records": int(tier2_escalation.sum()),
        "percentage": round(tier2_escalation.mean() * 100, 2),
        "required_fields": "risk_classification, delay_probability",
        "status": "EVALUATABLE",
        "limitation": "Condition is evaluatable, but actual operational escalation is not recorded."
    },
]

matrix = pd.DataFrame(rules)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

matrix.to_csv(OUTPUT_PATH, index=False)

print("\n========== BUSINESS RULE VALIDATION MATRIX ==========")

print(
    matrix[
        [
            "rule_id",
            "rule_name",
            "matching_records",
            "percentage",
            "status",
        ]
    ].to_string(index=False)
)

print("\n========== DOCUMENTED LIMITATIONS ==========")

for rule in rules:
    print(f"\n{rule['rule_id']}: {rule['limitation']}")

print("\nMatrix saved successfully:")
print(OUTPUT_PATH)
