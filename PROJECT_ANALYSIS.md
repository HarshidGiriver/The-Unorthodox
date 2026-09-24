# Project analysis: The-Unorthodox

Reviewed on 24 September 2026. Scope: all 41 tracked project files, including Python source, configuration, styles, notebook cells and saved outputs, the complete CSV, serialized model objects, and image integrity/metadata. Git internals and generated Python/test caches are described separately; Git object history was not audited. Images were checked for format integrity and dimensions, not subjected to visual design QA. No application code or model artifacts were changed.

## Assessment

This is a working Streamlit demonstration of financial distress scoring and loan restructuring, branded **Kintsugi AI** in the UI and **FinSafe AI** in documentation/backend metadata. Its strongest implemented capabilities are data transformation, local Isolation Forest inference, interactive portfolio exploration, and deterministic amortization. It is not yet an operational loan servicing system: authentication, persistent approvals, customer-specific authorization, actual email/SMS delivery, and an audit ledger are absent.

The three “agents” are ordinary Python classes called synchronously inside one application process. There is no independent backend server, agent orchestration runtime, database, or background queue.

## Architecture and execution

```text
frontend/app.py
  -> integration/services.py: load_and_score_portfolio()
     -> backend/data/loader.py: load CSV and construct borrower records
     -> backend/agents/detection_agent.py
        -> backend/data/feature_engineering.py: seven model features
        -> models/scaler.joblib -> models/isolation_forest.joblib
  -> frontend/components/bank_view.py
     -> backend/utils/metrics.py
     -> backend/agents/restructuring_agent.py
     -> backend/agents/outreach_agent.py -> optional external LLM request
  -> frontend/components/customer_view.py
     -> backend/agents/restructuring_agent.py
```

Portfolio results are cached in Streamlit for 600 seconds. Refresh buttons clear that cache. Restructuring recalculates on widget reruns. Outreach generation also runs on underwriter-view reruns, so configuring an API key can cause repeated external requests while interacting with the dashboard.

## Every folder and file

Paths below are relative to the project root. Each tracked file appears once in this inventory.

### Root and hidden configuration — 7 files

| File | Purpose and observations |
|---|---|
| `README.md` | Architecture, setup, dataset attribution, charts, and capability claims. Useful starting point, but overstates production readiness and compliance enforcement. Says 9 tests and 100% coverage; current suite has 10 tests and no coverage measurement. Links to an absent LICENSE. |
| `requirements.txt` | Runtime, plotting, test, and lint dependencies together. Uses minimum versions, not pinned versions despite the README description. |
| `pyproject.toml` | Setuptools package, Python >=3.10, runtime/dev dependencies and pytest settings. Discovers backend/frontend/integration packages; only frontend CSS is explicitly included as package data. Root assets, dataset and models are not packaged by these rules. Its Flake8 settings are not consumed by the shown CI invocations; CI explicitly passes its own options. |
| `.env.example` | API settings, model paths, contact hours and bank contact placeholders. The sample API key uses `your_...`, while the outreach placeholder filter checks `your-...`; copying the example can trigger a failed API request before fallback. |
| `.gitignore` | Excludes environments, caches, build products and `.env`; explicitly keeps the bundled marketing CSV. |
| `.github/workflows/ci.yml` | Push/PR CI on main/master, Python 3.10–3.12, install, critical lint, advisory lint, tests and backend imports. Does not build/install a wheel, measure coverage, or test actual delivery/persistence. |
| `.streamlit/config.toml` | Beige/green theme, headless mode; explicitly disables both CORS and XSRF protection. Reconsider this deployment configuration before exposing a stateful authenticated version. |

### `backend/` — 4 files

| File | Purpose and observations |
|---|---|
| `backend/__init__.py` | Package documentation and version `0.1.0`. |
| `backend/config.py` | Loads dotenv, resolves root data/model directories, defines seven features, tier boundaries, and restructuring constraints. Parses settings at import time. Relative model overrides resolve against the process working directory. Some declared lower-bound/default constants are unused. |
| `backend/train_models.py` | Loads data, computes features, fits RobustScaler and 150-tree IsolationForest with contamination 0.15 and random seed 42, serializes both artifacts. No holdout evaluation or provenance manifest. Creates the default models folder but not arbitrary override parent directories. |
| `backend/generate_visualizations.py` | Scores the portfolio and renders three static analysis charts; reports latency and cohort counts. Some annotations are hard-coded, including +151% deal reliance and 1,904/336 group labels, so regenerated charts can contain stale claims after data/model changes. |

### `backend/agents/` — 4 files

| File | Purpose and observations |
|---|---|
| `__init__.py` | Re-exports the three agent classes. |
| `detection_agent.py` | Loads model/scaler, scores portfolios in batches or individual rows, assigns tiers, and creates rule-based explanatory labels. On unavailable artifacts it substitutes heuristic scoring. Explanations are threshold rules, not model attribution. The individual scoring method expects engineered fields when a model is loaded. |
| `restructuring_agent.py` | EMI formula, amortization schedules, and a tenure search in six-month increments. Ordinary tested schedules conserve principal and finish at zero. Validation and moratorium-aware optimization need correction; detailed examples below. |
| `outreach_agent.py` | English/Hindi templates, optional HTTP LLM generation, and a contact-time flag. Does not send messages or enqueue them. Does not validate generated disclosures or enforce time restrictions. `channel` is accepted but unused. API exceptions are silently replaced by templates. |

### `backend/data/` — 3 files

| File | Purpose and observations |
|---|---|
| `__init__.py` | Re-exports loading, synthetic generation, schema checking and feature engineering. |
| `loader.py` | Tries tab/semicolon/comma input; maps marketing data into borrower records; synthesizes identities, loans, savings, credit utilization and late days. Retains all source columns. Missing files silently produce 300 synthetic borrowers, including explicitly requested nonexistent paths. Schema validation checks column presence only. |
| `feature_engineering.py` | Computes expense/income and EMI ratios, total outflow, liquidity runway, depletion, deal reliance, credit utilization and a heuristic 0–100 stress index. Provides matrix extraction in a fixed feature order. Clipping guards some division edge cases but does not validate all NaN/infinite/type problems. Optional-column branches use scalar defaults followed by `.astype()`, which fail when those columns are absent. |

### `backend/utils/` — 2 files

| File | Purpose and observations |
|---|---|
| `__init__.py` | Re-exports portfolio KPI calculation. |
| `metrics.py` | Calculates portfolio totals, tier exposure, anomaly prevalence, a blended late-days/stress exposure, and projected NPA avoidance. The exposure labelled PAR30 includes stress >=75 even without 30 late days. NPA avoidance is a fixed 68% multiplier, not an evaluated forecast. Missing risk labels produce invented 70/20/10-like counts. Some fallback Series assume a default index. |

### `frontend/`, `frontend/components/`, `frontend/styles/` — 6 files

| File | Purpose and observations |
|---|---|
| `frontend/__init__.py` | Presentation package marker. |
| `frontend/app.py` | Entry point; loads CSS/logo, caches scoring, builds sidebar/search/quick actions, and switches among underwriter, customer, and architecture views. Compliance/session badges are static presentation, not authentication or verification. |
| `frontend/components/__init__.py` | Re-exports both screen renderers. |
| `frontend/components/bank_view.py` | KPI cards, Plotly charts, filters, borrower details, restructuring sliders, outreach preview and approval banner. Search treats text as regex and can crash. Approval only renders UI feedback. Deep-dive selection defaults to CUST-4141; an empty filtered table falls back to the entire portfolio for case selection. Every risk badge uses tier-3 styling regardless of actual tier. |
| `frontend/components/customer_view.py` | Demo account selector, relief sliders, repayment chart, interest disclosures, consent checkbox and activation banner. No ownership checks or persisted consent/activation. Consent is not tied to an immutable version of the selected terms. Empty portfolios are not handled before accessing a customer row. |
| `frontend/styles/custom.css` | Extensive pine/gold/beige design system, glass panels, typography, widgets, badges and animation. Imports Google Fonts; uses many `!important` overrides and Streamlit internal selectors. Contains tab styling although navigation uses a radio widget. No responsive media queries or reduced-motion overrides; mobile appearance needs browser-level verification. |

### `integration/` — 2 files

| File | Purpose and observations |
|---|---|
| `__init__.py` | Application-service package marker. |
| `services.py` | Thin frontend/backend boundary: loads and scores a portfolio and re-exports agents/KPI helper. Keeps Streamlit out of backend services, but does not implement approval, storage or dispatch workflows. |

### `data/raw/` — 1 file

`marketing_campaign.csv`: tab-delimited, **2,240 rows × 29 columns**. All customer IDs are unique; **24 Income entries are missing** and imputed by the loader. Columns cover identity/demographics, enrollment date, recency, six spending categories, purchase channels, campaign acceptance, complaints, constants and response. This is marketing customer data; the application constructs the loan-servicing fields.

The loader explicitly treats `Income` directly as monthly income and the six category totals as monthly expenses. This is a simulation convention in code, not a verified source-unit conversion. Tests enforce that convention. Preserve it deliberately or revise the data contract and tests together after checking source semantics.

### `models/` — 2 files

| File | Verified contents |
|---|---|
| `isolation_forest.joblib` | Successfully loaded IsolationForest: 150 estimators, contamination 0.15, max_samples auto, random_state 42, n_jobs -1, seven input features. |
| `scaler.joblib` | Successfully loaded fitted RobustScaler with seven centers/scales. Median EMI burden is approximately 0.2803 and median runway 2.545 months, consistent with the current data scale rather than the stale notebook output. |

There is no adjacent metadata recording training dependency versions, dataset hash, feature schema version or evaluation provenance. Runtime loading succeeded in this environment, but unrestricted dependency upgrades reduce reproducibility. Joblib artifacts should remain trusted project inputs.

### `notebooks/` — 1 file

`01_exploratory_stress.ipynb`: **16 cells** covering ingestion, features, model theory/scoring, display of saved charts, and exact cohort assertions. Saved outputs are stale: they show 16 loaded attributes and income divided to a different scale, whereas the current loader retains raw columns and treats Income directly as monthly. No SHAP analysis is implemented despite the README tree description. Claims of detecting distress 30–60 days before default are not backed by temporal outcome validation in the repository.

### `assets/` — 5 files

| File | Dimensions | Role |
|---|---:|---|
| `kintsugi_logo.jpg` | 1024 × 1024 | Original brand image; fallback in sidebar. |
| `kintsugi_logo_thumb.png` | 400 × 400 | Preferred sidebar logo. |
| `distress_distribution.png` | 3570 × 1920 | Saved anomaly distribution chart for README/notebook. |
| `deal_vs_spend_scatter.png` | 3570 × 1920 | Saved deal-reliance/discretionary-spending chart. |
| `risk_drivers_comparison.png` | 4770 × 1653 | Saved cohort comparison chart. |

All five image files passed format integrity checks. These static analysis charts are separate from the live Plotly UI charts.

### `tests/` — 4 files

| File | Coverage actually implemented |
|---|---|
| `__init__.py` | Test package marker. |
| `test_app.py` | One smoke test renders all three views with external LLM calls disabled. Does not assert approvals, deliveries, search edge cases or styling. |
| `test_features.py` | Five tests: ordinary ratios, zero-income safety, heuristic monotonicity, dataset mapping, and source-record traceability. |
| `test_restructuring.py` | Four tests: EMI formula, ordinary schedule invariance, decreasing EMI with longer tenure, and principal freeze under a valid moratorium. |

### Generated and repository metadata folders

`.git/` contains Git configuration, refs, logs, index, object storage, hook samples and fetch/commit metadata. These support version control rather than runtime behavior; historical objects were not individually reviewed. `__pycache__/` directories contain disposable interpreter-specific compiled modules. `.pytest_cache/` is generated by testing. None is a separate project or application module. No AGENTS.md instructions were found in the project inventory.

## Prioritized findings

### High: apparent business actions are only presentation

`bank_view.py:367` and `customer_view.py:232` display activation, dispatch and ledger-update success without corresponding state changes. Refresh loses the apparent result. There is no durable plan ID, approval state, delivery receipt, queue or audit entry. Either label these actions explicitly as simulations or implement the complete workflow before presenting them as completed transactions.

### High: distress validation is circular and incomplete

`loader.py:154` defines strain from deal reliance >0.40, then generates low savings, depletion and high utilization conditioned on that rule. The detector consumes these generated variables. Separation in the charts therefore partly demonstrates the assumptions that created the data. A configured 15% contamination rate and 336 detected anomalies are not evidence of predictive accuracy, future defaults, or successful intervention. No default labels, temporal holdout, precision/recall evaluation or intervention outcomes are present. Model anomaly scores are mapped through custom constants; they are not calibrated default probabilities.

### High: restructuring boundary and target errors

The automatic tenure search (`restructuring_agent.py:148`) evaluates EMI over the full new tenure, but the final calculation subtracts the moratorium from repayment months. Reproduced with principal 300,000, EMI 14,400, 24 months, APR 14%, default 25% reduction target and six moratorium months: the solver selects 36 total months and EMI **11,909.51**, only **17.3% reduction**.

A direct six-month schedule with six moratorium months returns an ending balance of **300,000**, contradicting the unconditional terminal-zero guarantee. Negative concessions/extensions/moratoria are not rejected. The fixed 6% minimum rate can also increase a loan already below 6%, even when no concession is requested. Validate input domains, require active repayment months, use active tenure in the search and report whether a target is feasible.

Baseline data specifies EMI 14,400 for 300,000 at 14% over 24 months; the solver calculates **14,403.86**. This small inconsistency affects old-versus-new interest comparisons. Moratorium means interest-only servicing here, not a full payment holiday.

### High: compliance labels exceed implemented controls

The timing check uses server-local time, returns a Boolean and does not gate the approval button. The “queue for 08:00” text has no queue behind it. Templates omit lifetime interest comparisons; generated LLM text is not checked for required disclosures and its prompt does not supply grievance details. Static “verified” and “audit verified” badges are not evidence of verification. This is a finding about code versus repository claims, not a legal assessment of current RBI requirements.

### Medium: ordinary search input crashes the screen

Reproduced through Streamlit AppTest: entering `[` in `triage_local_search` raises `Invalid regular expression: missing ]: [`. All three `str.contains` calls at `bank_view.py:195` use default regex behavior. Use literal matching for ordinary user search.

### Medium: data errors can silently change the application mode

A missing CSV becomes 300 synthetic records; missing/unreadable models become heuristic scoring. The UI still presents an Isolation Forest system. Make simulation/fallback mode explicit and distinguish an absent optional demo asset from a requested path that is invalid. Validate value types, ranges, finite numbers and duplicate identities rather than only column names.

The heuristic anomaly threshold is 0.55 while Tier 3 starts at 0.65, so anomaly counts and severe-tier counts diverge in fallback mode.

### Medium: metrics and disclosures need precise labels

The displayed PAR30 metric combines late-days history with a heuristic stress threshold. The 68% cure factor is hard-coded without a supporting study in the repository. “Deal Surge” compares a customer with a fixed cohort number, not that customer's historical change. Label these as simulation assumptions/proxies and compute dynamic cohort benchmarks where appropriate.

### Medium: operational and packaging gaps

Both personas can view all demo borrowers without authentication. There is no role separation, durable consent, audit trail, or authorization around approvals. HTML interpolates record/config values without explicit escaping. Deployment protections are disabled. A packaged installation would also lack root runtime data/model/image resources under the shown package-data rules; package installation was not built/tested in this review.

### Lower: maintenance and reproducibility

Unify FinSafe/Kintsugi names and version labels, add the missing license file if intended, correct test/coverage claims, refresh notebook outputs, remove stale chart annotations, and record model provenance. Consider reducing extensive inline HTML/CSS duplication and add targeted interaction tests. Pydantic is declared but no Pydantic schema is used.

## Verification performed

- `python -m pytest -q`: **10 passed in 12.88 seconds** on Python **3.14.7**.
- Test run produced **903 warnings**, from joblib deserialization using a NumPy shape assignment deprecated in the installed environment.
- Critical CI-equivalent lint (`E9,F63,F7,F82`): **0 findings**.
- Loaded both serialized artifacts and scored all 2,240 accounts: **1,212 Tier 1; 692 Tier 2; 336 Tier 3**, matching README counts.
- Validated CSV dimensions, missing values and ID uniqueness; verified all image formats/dimensions.
- Confirmed the quick-action simulator navigation works in the current environment.
- Reproduced malformed-search failure, missed EMI reduction target, and nonzero ending balance for an all-moratorium schedule.

The existing tests establish basic demo functionality, not complete correctness or 100% coverage. This review did not send outreach, call the external LLM, retrain models, regenerate charts, audit legal compliance, or test a deployed browser/mobile layout.

## Suggested implementation order

1. Make simulated approvals/delivery and synthetic financial data explicit in the UI.
2. Fix search escaping, solver validation and moratorium-aware target calculations; add focused regression tests.
3. Enforce data contracts and surface fallback status; reconcile baseline loan terms.
4. Add real identity, authorization, durable plan/consent state and delivery/audit workflows if operational use is intended.
5. Establish real outcome-based model evaluation and versioned training artifacts.
6. Align documentation, notebook outputs, packaging and deployment settings with verified behavior.
