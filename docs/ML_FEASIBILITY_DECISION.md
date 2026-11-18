# ML Feasibility Assessment — ColdChain-AI

## Decision

Predictive machine learning is not approved for production
use with the current dataset.

The available evidence does not demonstrate sufficient
predictive signal for the tested target:
`delivery_time_deviation`.

## Experiments conducted

### 1. Linear Regression

- Chronological 80/20 split
- 18 operational features
- MAE: 3.698446
- RMSE: 4.167392
- R2: -0.001873

### 2. ExtraTrees Regression

- Same chronological split
- Same 18 operational features
- 300-tree ensemble
- MAE: 3.713070
- RMSE: 4.181086
- R2: -0.008468

### 3. Mean Baseline

- MAE: 3.695906
- RMSE: 4.163646
- R2: -0.000073

## Findings

1. Neither regression model outperformed the mean baseline.
2. Linear and nonlinear predictive relationships appear weak.
3. Feature importances from ExtraTrees were nearly uniform.
4. Previous correlation and temporal audits also showed
   negligible relationships.
5. The methodology used to generate target variables is
   undocumented.
6. The dataset does not contain a shipment identifier.

## Engineering Decision

Do not promote the current regression models to production.

Do not claim reliable delay prediction using this dataset.

Continue development of:

- SQL-based operational analytics.
- SOP-driven rule-based escalation.
- Policy document retrieval (RAG).
- LLM-powered operational assistance.
- API and frontend integration.

Reconsider predictive ML when a dataset with verified
shipment-level outcomes and documented target-generation
methodology becomes available.

## Limitations

These experiments do not prove that the dataset is synthetic
or that all possible machine learning approaches will fail.

The decision is based on the absence of demonstrated
predictive performance in the experiments conducted.