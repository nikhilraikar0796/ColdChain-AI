\# Phase 3 — SOP-Driven Rule Engine and Reporting



\## 1. Objective



Implement a deterministic, explainable operational rule engine based on the Cold Chain Incident SOP.



The engine evaluates logistics telemetry records, identifies operational escalation candidates, handles missing information explicitly, and generates structured reports.



The LLM is not responsible for deciding whether a business rule has triggered. Rule evaluation is performed by Python code.



\## 2. Architecture



SQL Server Semantic Views

→ Restricted SQL Agent Account

→ Python Data Retrieval

→ Cold Chain Rule Engine

→ Rule Evaluation Results

→ SQL Cross-Validation

→ JSON and CSV Reports



\### Key components



\- `app/rules/models.py` — rule definitions, statuses, severity and result models.

\- `app/rules/conditions.py` — reusable condition evaluators and AND logic.

\- `app/rules/registry.py` — central catalogue of operational rules.

\- `app/rules/engine.py` — rule evaluation implementation.

\- `app/rules/reporting.py` — JSON and CSV report generation.

\- `scripts/run\_rule\_engine.py` — SQL Server integration and execution.

\- `scripts/verify\_rule\_reports.py` — generated report validation.

\- `tests/test\_rule\_engine.py` — unit tests.



\## 3. Implemented Business Rules



\### CC-001: Tier 2 Logistics Escalation



Condition:



\- Risk classification is `High Risk`.

\- Delay probability is strictly greater than `0.65`.



Recommended action:



Refer the record to the Tier 2 Logistics Manager as an escalation candidate.



Important limitation:



The dataset does not record actual escalation status. The rule identifies candidates; it does not prove that an escalation occurred.



\### CC-002: Fresh Perishable Temperature Breach



Conditions:



\- Cargo category is fresh perishables.

\- IoT temperature is strictly greater than 4°C.



Recommended action:



Contact the driver and verify auxiliary cooling. Consider emergency cold-storage diversion only after confirming an ETA delay greater than one hour.



Important limitation:



The dataset does not contain cargo category. Temperature readings alone cannot establish that a cold-chain breach occurred.



Consequently, this rule returns `NOT\_EVALUABLE` when cargo category is unavailable.



\### CC-003: LA/Long Beach Port Congestion Diversion



Conditions:



\- Port identity is Los Angeles or Long Beach.

\- Port congestion level is strictly greater than 7.



Recommended action:



Suspend the standard route and consider diversion to the Inland Empire Overflow Depot in San Bernardino.



Important limitation:



The dataset does not contain port identity. Congestion readings cannot independently establish that a shipment belongs to either port.



Consequently, this rule returns `NOT\_EVALUABLE` when port identity is unavailable.



\## 4. Rule Evaluation Semantics



Each condition returns one of three statuses:



\- `TRIGGERED` — the condition is satisfied.

\- `NOT\_TRIGGERED` — the condition is false.

\- `NOT\_EVALUABLE` — required information is unavailable or invalid.



For combined AND conditions:



1\. If any condition is false, the combined result is `NOT\_TRIGGERED`.

2\. If no condition is false but at least one condition is unknown, the result is `NOT\_EVALUABLE`.

3\. The result is `TRIGGERED` only when every condition is satisfied.



This prevents missing information from being silently interpreted as a successful business-rule evaluation.



\## 5. SQL Server Integration



The engine reads operational records from:



`agent\_views.vw\_telemetry\_overview`



It cross-checks Tier 2 candidates against:



`agent\_views.vw\_tier2\_escalation\_candidates`



The integration uses a restricted SQL Server account with read-only access to the approved semantic views.



Direct access to the underlying operational table is denied.



Write and schema-modification permissions are not granted.



Credentials are collected securely at runtime using Python `getpass` during this development stage.



\## 6. Validation Results



Dataset records evaluated: 32,065



Rules evaluated per record: 3



Total rule evaluations: 96,195



\### Rule evaluation summary



| Rule | Triggered | Not Triggered | Not Evaluable |

|---|---:|---:|---:|

| CC-001 | 15,440 | 16,625 | 0 |

| CC-002 | 0 | 23,391 | 8,674 |

| CC-003 | 0 | 12,499 | 19,566 |



\### SQL versus Python validation



\- SQL Tier 2 candidates: 15,440

\- Python Tier 2 candidates: 15,440

\- Missing record IDs in Python: 0

\- Extra record IDs in Python: 0



The record-level comparison passed.



\### Unit testing



All 15 rule-engine unit tests passed.



\### Report validation



Both generated reports passed validation:



\- `data/processed/rule\_evaluation\_report.json`

\- `data/processed/triggered\_alerts.csv`



The reports are generated locally and excluded from Git.



\## 7. Engineering Decisions



\- Deterministic Python rules are used for business-critical conditions.

\- Missing operational context is represented explicitly.

\- SQL Server semantic views provide a controlled data-access boundary.

\- SQL and Python results are compared at the record-ID level.

\- JSON provides structured evaluation metadata and triggered alerts.

\- CSV provides an operationally accessible alert export.

\- Predictive ML is not used for production decisions because the current dataset did not demonstrate sufficient predictive signal.



\## 8. Known Limitations



1\. Cargo category is unavailable.

2\. Port identity is unavailable.

3\. Actual escalation completion status is unavailable.

4\. ETA variation semantics require further operational verification.

5\. The dataset has no shipment identifier, so individual telemetry records should not automatically be interpreted as independent shipments.

6\. The current rule engine is an operational decision-support component, not an automated dispatch or escalation execution system.



\## 9. Next Phase



Phase 4 will introduce an AI agent using Groq and LangGraph.



The agent will be able to:



\- Query approved SQL semantic views.

\- Retrieve relevant SOP documentation through RAG.

\- Explain deterministic rule-engine results.

\- Provide operational context using weather information.

\- Coordinate multiple tools through an agent workflow.



The AI agent must preserve the deterministic rule engine as the source of truth for SOP rule outcomes.
