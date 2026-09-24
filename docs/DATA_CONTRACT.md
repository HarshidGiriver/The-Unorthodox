# Borrower data contract

Monetary inputs are INR. Income, expenses and EMI are monthly amounts; savings and principal are point-in-time balances. APR is a fraction (0.14 = 14%). Tenure is whole months; late days are a count over the previous six months.

Required text: `customer_id` (unique, nonempty) and `name` (nonempty).

| Required numeric fields | Accepted values |
|---|---|
| monthly_income, monthly_expenses, savings_balance, previous_savings_balance | Finite, >=0 |
| current_emi, remaining_principal | Finite, >=0.01 |
| remaining_tenure_months | Integer 1–1200 |
| annual_interest_rate | Fraction 0–1 |
| deal_purchase_ratio | Fraction 0–1 |
| credit_utilization | Fraction 0–2 |
| late_payment_days_last_6m | Integer 0–184 |

Numeric strings are normalized. Missing required values, infinities, invalid strings, duplicate IDs and empty datasets fail validation. Supplied finances must describe the same loan; the application does not infer fees, variable-rate structures or payment allocation rules.

## Source versus simulation

For marketing data, IDs, demographics, campaign responses, purchase counts and category spending are source fields. Deal ratio, discretionary share and dependent counts are derived. Names/phones, principal/APR/tenure/EMI, savings history, utilization and late days are generated. Income is used directly as monthly INR as a simulation convention. Spending totals are similarly treated as monthly; source-unit conversion is not asserted. Missing Income is median-imputed (24 records in the bundled file). All-missing Income uses a simulation default of 50,000.

Frames carry `data_source`, `simulation`, `data_warning`, and `imputed_income_count` attributes. Scoring adds `scoring_mode`, `model_version`, and warnings. Persistent imports retain required financial fields and a simulation flag; generated source phones are never imported as verified contacts.

## Optional evaluation fields

`observed_default`: complete observed 0/1 outcomes from a known future horizon; never fabricate these from anomaly scores. `snapshot_date`: timestamp at which predictors became available. Equal snapshot dates remain in the same split. These fields are not predictors. Assess cohorts, label maturity and leakage before interpreting metrics as predictive evidence.

## Repayment contract

Moratoria are interest-only periods included in total tenure, not payment holidays. At least one repayment month must remain. Extension is 0–36 months, concession 0–200 basis points and moratorium 0–6 months. Automatic optimization searches every permitted extension using active repayment months and reports `target_met`. Zero-interest loans work; concessions never increase rates. Final payments adjust rounding; compare full schedules for lifetime interest.
