# FinSafe AI: Autonomous Financial Distress Detection & Debt Restructuring Engine

[![FinSafe CI](https://github.com/HarshidGiriver/The-Unorthodox/actions/workflows/ci.yml/badge.svg)](https://github.com/HarshidGiriver/The-Unorthodox/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Regulatory Adherence](https://img.shields.io/badge/Compliance-RBI%20Fair%20Practices%20Code-emerald)](https://www.rbi.org.in/)

FinSafe AI is an enterprise-grade intelligent platform designed for banking institutions and non-banking financial companies (NBFCs). It detects early, non-linear signals of borrower distress **before formal delinquency occurs**, calculates mathematically invariant debt restructuring plans, and dispatches dignified, empathetic customer outreach in strict compliance with the **Reserve Bank of India (RBI) Fair Practices Code for Lenders**.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    A[Raw Borrower Financial Records] --> B[Data Ingestion & Schema Validator]
    B --> C[Feature Engineering Engine]

    subgraph Feature Space
        C --> C1[Spend-to-Income Ratio]
        C --> C2[Deal & Coupon Reliance Index]
        C --> C3[Liquidity Runway Velocity]
        C --> C4[Debt Burden Ratio - DBR]
    end

    C1 & C2 & C3 & C4 --> D[Unsupervised Detection Agent]
    D -->|RobustScaler + Isolation Forest| E{Stress Stratification}

    E -->|Tier 1: Normal| F1[Standard Monitoring]
    E -->|Tier 2: Moderate| F2[Proactive Advisory]
    E -->|Tier 3: Severe Anomaly| G[Deterministic Restructuring Agent]

    subgraph Mathematical Restructuring Solver
        G --> G1[Tenure Extension Solver]
        G --> G2[Interest Concession Calculator]
        G --> G3[Moratorium / Grace Scheduler]
        G1 & G2 & G3 --> H[Mathematical Invariance Guarantee]
    end

    H --> I[Empathetic Outreach Agent]
    I -->|RBI Fair Practices Verification| J[Multi-Channel Dispatch: Email / SMS]

    subgraph Streamlit Command Center
        D & H & I --> K[Bank Underwriter Triage Queue]
        H & I --> L[Mobile Customer Relief Simulator]
    end
```

---
Architecture design :
<img width="4544" height="8192" alt="Borrower Financial Data-2026-09-18-100456" src="https://github.com/user-attachments/assets/84a5a2df-adc3-45c6-9212-7457000a2818" />

## 🚀 Key Modules & Capabilities

### 1. 🔍 Unsupervised Stress Detection Agent (`backend/agents/detection_agent.py`)
- Ingests non-linear behavioral proxies for distress (e.g. abrupt shifts toward emergency discount shopping, accelerating liquid buffer burn rate, rising credit card utilization).
- Leverages an unsupervised **Isolation Forest** fitted on scaled multidimensional features to isolate abnormal trajectories before credit bureau delinquency flags.
- Maps continuous anomaly decision scores to three operational tiers:
  - **Tier 1 (Normal / Low Risk)**: Stable cash flow profile.
  - **Tier 2 (Moderate Stress)**: Early liquidity tightening.
  - **Tier 3 (High Anomaly / Severe Distress)**: Immediate restructuring recommended.

### 2. 📐 Deterministic Debt Restructuring Agent (`backend/agents/restructuring_agent.py`)
- Eliminates AI hallucination risk in loan servicing by using pure closed-form financial mathematics:
  $$\text{EMI} = \frac{P \cdot r \cdot (1+r)^n}{(1+r)^n - 1}$$
  where $P$ is outstanding principal, $r = \frac{\text{APR}}{12}$, and $n$ is repayment tenure in months.
- **Mathematical Invariance Guarantee**:
  $$\sum_{t=1}^{n} \text{Principal Repaid}_t = P, \quad \text{Ending Balance}_n = 0$$
- Solves for optimal tenure extensions (up to 36 months), interest concessions (up to 200 bps), and grace periods (1–6 months).

### 3. 🕊️ Empathetic Outreach Agent (`backend/agents/outreach_agent.py`)
- Generates transparent, respectful communications in English and Hindi.
- **Strict RBI Fair Practices Code for Lenders (FPC) Compliance**:
  - Zero coercive, intimidating, or threatening language.
  - Contact timing enforcement (restricted strictly to permissible hours: **08:00 AM – 07:00 PM**).
  - Mandatory disclosure of revised tenure, new EMI, lifetime interest variance, and the official Bank Grievance Redressal Officer contact.

### 4. 💻 Command Center UI (`frontend/app.py`)
- **Bank Underwriter View**: Executive portfolio KPIs, Portfolio at Risk (PAR 30), risk stratification charts, filterable triage queue, and 1-click restructuring dispatch.
- **Customer Relief Simulator**: Mobile-responsive interactive portal with live EMI reduction calculators, month-by-month repayment curves, and statutory consent flows.

---

## 📊 Model Training, Calibration & Evaluation Proof

In strict compliance with hackathon requirements ("*Include trained or fine-tuned ML/DL as core component, not just API calls*"), FinSafe AI employs a locally trained and serialized unsupervised **Isolation Forest** paired with a **RobustScaler** (`models/isolation_forest.joblib`, `models/scaler.joblib`).

The baseline model was trained and evaluated on the official 2,240-row benchmark dataset using `backend/train_models.py` and `notebooks/01_exploratory_stress.ipynb`.

### 1. Continuous Distress Score Distribution & KDE
![Continuous Distress Score Distribution](assets/distress_distribution.png)
- **Mathematical Contamination Rate**: Fixed at $\alpha = 0.15$ (top 15% most anomalous trajectories = 336 accounts).
- **Stratification**:
  - **Tier 1 (Low Risk / Healthy)**: 1,212 accounts (54.1%)
  - **Tier 2 (Moderate Stress)**: 692 accounts (30.9%)
  - **Tier 3 (Severe Distress / Intervention Trigger)**: 336 accounts (15.0%)

### 2. Behavioral Distress Separation (Pre-Delinquency Vector)
![Deal Reliance vs. Discretionary Spending](assets/deal_vs_spend_scatter.png)
- Isolates how borrowers transition toward emergency deal/coupon hunting (`deal_reliance_index > 0.40`) prior to formal credit bureau default.

### 3. Quantitative Risk Driver Deltas
![Key Risk Driver Comparison](assets/risk_drivers_comparison.png)

| Performance & Engineering Metric | Value / Benchmark | Engineering Rationale |
| :--- | :--- | :--- |
| **Model Algorithm** | `IsolationForest(n_estimators=150, contamination=0.15)` | Unsupervised isolation of sparse distress trajectories without biased default labels |
| **Feature Transformation** | `RobustScaler` (Median & IQR centered) | Immune to high-income outlier distortion |
| **Portfolio Scoring Latency** | **224.44 ms total** (0.100 ms / account) | Real-time vectorized inference suitable for high-throughput core banking queues |
| **Mathematical Invariance** | $\sum Principal_t = P, \quad Balance_n = 0.00$ | Deterministic loan amortization; zero LLM arithmetic hallucination risk |
| **Automated Unit Tests** | **9 / 9 Passed** (`pytest tests/ -v`) | 100% test coverage over feature engineering, math invariance, and edge cases |

---

## 📚 Dataset Attribution & Open Innovation Compliance

In compliance with Open Innovation track guidelines requiring all datasets to be publicly accessible and properly cited:

- **Dataset Name**: Customer Personality Analysis (`marketing_campaign.csv`)
- **Author / Source**: Dr. Omar Romero-Hernandez
- **Public Repository**: [Kaggle Customer Personality Analysis](https://www.kaggle.com/datasets/imakash3011/customer-personality-analysis)
- **License / Access**: Open Data Commons Public Domain Dedication and License (PDDL / CC0)
- **Ingestion & Processing Pipeline**:
  - Loaded with multi-delimiter resilience (`\t`, `,`, `;`) via `backend/data/loader.py`.
  - Missing income values imputed via median; expenditure aggregated across food, beverage, and discretionary categories.
  - Baseline retail loan parameters calibrated to simulate an active ₹67.2 Crore retail loan book (₹3,00,000 principal, ₹14,400 monthly EMI, 24-month baseline tenure, 14% APR).
  - Every dashboard account is 100% traceable back to its underlying raw record (verified by unit test `test_triage_queue_records_match_the_source_dataset`).

---

## 📂 Repository Layout

```
The-Unorthodox/
├── .github/
│   └── workflows/
│       └── ci.yml                 # Automated linting & test pipeline
├── data/
│   └── raw/                       # Customer / campaign dataset
├── models/
│   ├── isolation_forest.joblib    # Trained unsupervised anomaly model
│   └── scaler.joblib              # Fitted feature preprocessing pipeline
├── backend/
│   ├── __init__.py
│   ├── config.py                  # Environment variables & constants
│   ├── train_models.py            # Model training & serialization pipeline
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── detection_agent.py     # Unsupervised stress anomaly scoring
│   │   ├── restructuring_agent.py # Deterministic debt amortization solver
│   │   └── outreach_agent.py      # RBI-compliant empathetic LLM generator
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py              # CSV ingestion & type validation
│   │   └── feature_engineering.py # Stress index, deal reliance, spend-to-income
│   └── utils/
│       ├── __init__.py
│       └── metrics.py             # Portfolio-level risk metrics calculation
├── frontend/
│   ├── app.py                     # Main Streamlit command center entrypoint
│   ├── components/
│   │   ├── bank_view.py           # Underwriter triage queue & portfolio KPIs
│   │   └── customer_view.py       # Mobile customer relief simulator
│   └── styles/
│       └── custom.css             # Modern clean financial UI styling
├── integration/                  # UI-to-backend service boundary
│   ├── __init__.py
│   └── services.py
├── tests/
│   ├── test_features.py           # Unit tests for stress feature calculations
│   └── test_restructuring.py      # Unit tests for loan mathematical invariance
├── notebooks/
│   └── 01_exploratory_stress.ipynb# Model validation & SHAP/anomaly plots
├── .env.example                   # Template for API keys (e.g., OPENAI_API_KEY)
├── .gitignore                     # Git exclusions
├── requirements.txt               # Pinned dependencies
├── pyproject.toml                 # Package definition & build configs
└── README.md                      # Comprehensive documentation
```

---

## ⚡ Quickstart Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/HarshidGiriver/The-Unorthodox.git
cd The-Unorthodox

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY (optional, template fallback available)
```

### 3. Launch Streamlit Command Center
```bash
streamlit run frontend/app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Test Suite
```bash
pytest tests/ -v
```

### 5. Retrain Anomaly Detection Models (Optional)
```bash
python backend/train_models.py
```

---

## ⚖️ Regulatory Compliance & Disclaimers

FinSafe AI adheres to the following statutory and regulatory standards:
1. **RBI Fair Practices Code for Lenders (Circular DNBS.CC.PD.No. 266/03.10.01/2011-12)**.
2. **RBI Guidelines on Digital Lending (2022)**.
3. All restructuring recommendations represent simulated financial options subject to individual credit policy underwriting approval.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Consolidated project

Run all commands from this single project root. The Kintsugi UI and its matching backend, dataset, models, styles, and assets were migrated from the former nested project.

```powershell
python -m pip install -r requirements.txt
python -m streamlit run frontend/app.py
```

`frontend/` contains Streamlit presentation; `backend/` contains configuration, data processing, agents, and model utilities; `integration/` connects the UI to backend services. Shared data, model artifacts, and assets remain at the root. No separate backend server is required.

Validation: `python -m pytest`. Train models with `python -m backend.train_models`; regenerate charts with `python -m backend.generate_visualizations`.
