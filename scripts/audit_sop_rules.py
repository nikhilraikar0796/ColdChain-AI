
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

total = len(df)

def report_rule(name, condition, explanation):
    count = int(condition.sum())

    print(f"\n{name}")
    print(f"Matching records: {count:,}")
    print(f"Percentage: {count / total * 100:.2f}%")
    print(f"Interpretation: {explanation}")


print("\n========== SOP BUSINESS RULE AUDIT ==========")
print(f"Total records: {total:,}")

# --------------------------------------------------
# Rule 1: Temperature above 4°C
# --------------------------------------------------

temperature_breach = df["iot_temperature"] > 4

report_rule(
    "RULE 1: TEMPERATURE ABOVE 4°C",
    temperature_breach,
    "Potential breach only if the shipment contains fresh perishables."
)

# --------------------------------------------------
# Rule 2: Temperature breach + ETA variation > 1 hour
# --------------------------------------------------

temperature_and_eta = (
    temperature_breach
    & (df["eta_variation_hours"] > 1)
)

report_rule(
    "RULE 2: TEMPERATURE ABOVE 4°C AND ETA VARIATION ABOVE 1 HOUR",
    temperature_and_eta,
    "Potential emergency cold-storage diversion candidates; ETA field semantics require verification."
)

# --------------------------------------------------
# Rule 3: Port congestion above 7
# --------------------------------------------------

port_congestion = df["port_congestion_level"] > 7

report_rule(
    "RULE 3: PORT CONGESTION ABOVE 7",
    port_congestion,
    "Congestion threshold matches, but no port identifier exists to verify LA/Long Beach applicability."
)

# --------------------------------------------------
# Rule 4: High Risk + delay probability above 0.65
# --------------------------------------------------

tier2_escalation = (
    (df["risk_classification"] == "High Risk")
    & (df["delay_probability"] > 0.65)
)

report_rule(
    "RULE 4: HIGH RISK AND DELAY PROBABILITY ABOVE 0.65",
    tier2_escalation,
    "Matches the SOP's Tier 2 escalation condition."
)

# --------------------------------------------------
# Rule 5: Check whether required business fields exist
# --------------------------------------------------

required_fields = {
    "temperature": "iot_temperature",
    "port congestion": "port_congestion_level",
    "risk classification": "risk_classification",
    "delay probability": "delay_probability",
    "ETA variation": "eta_variation_hours",
    "port identity": "port_name",
    "cargo category": "cargo_type",
}

print("\n========== SOP FIELD AVAILABILITY ==========")

for business_term, column in required_fields.items():
    exists = column in df.columns

    print(
        f"{business_term}: "
        f"{'AVAILABLE' if exists else 'MISSING'}"
        f" ({column})"
    )

print("\nSOP business-rule audit completed.")
