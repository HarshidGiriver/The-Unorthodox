"""Data ingestion, schema validation, and synthetic data generation for Kintsugi AI."""

from typing import Tuple, List, Optional
from pathlib import Path
import numpy as np
import pandas as pd
from backend.config import RAW_DATA_DIR
from backend.finance import BASELINE_EMI, calculate_emi

REQUIRED_COLUMNS = [
    "customer_id",
    "name",
    "monthly_income",
    "monthly_expenses",
    "current_emi",
    "remaining_principal",
    "remaining_tenure_months",
    "annual_interest_rate",
    "savings_balance",
    "previous_savings_balance",
    "deal_purchase_ratio",
    "credit_utilization",
    "late_payment_days_last_6m",
]


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that DataFrame has all required columns and valid data types.

    Args:
        df: Input DataFrame to check.

    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    errors = [f"Missing column: {col}" for col in REQUIRED_COLUMNS if col not in df.columns]
    if errors:
        return False, errors
    if df.empty:
        errors.append("Dataset is empty")
    for col in ("customer_id", "name"):
        if df[col].isna().any() or not df[col].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
            errors.append(f"{col} must contain nonempty text")
    if df["customer_id"].duplicated().any():
        errors.append("customer_id must be unique")
    for col in REQUIRED_COLUMNS[2:]:
        values = pd.to_numeric(df[col], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            errors.append(f"{col} must contain finite numeric values with no missing entries")
            continue
        minimum = 0.01 if col in ("current_emi", "remaining_principal") else 0
        maximum = {"annual_interest_rate": 1, "deal_purchase_ratio": 1,
                   "credit_utilization": 2, "remaining_tenure_months": 1200,
                   "late_payment_days_last_6m": 184}.get(col)
        if (values < minimum).any() or (maximum is not None and (values > maximum).any()):
            errors.append(f"{col} is outside the allowed range")
        if col in ("remaining_tenure_months", "late_payment_days_last_6m"):
            if (values % 1 != 0).any() or (col == "remaining_tenure_months" and (values < 1).any()):
                errors.append(f"{col} must contain valid whole numbers")
    return not errors, errors


def normalize_customers(df):
    valid, errors = validate_schema(df)
    if not valid:
        raise ValueError("Invalid borrower data: " + "; ".join(errors))
    result = df.copy()
    for col in REQUIRED_COLUMNS[2:]:
        result[col] = pd.to_numeric(result[col])
    for col in ("remaining_tenure_months", "late_payment_days_last_6m"):
        result[col] = result[col].astype(int)
    return result


def load_raw_delimited_csv(file_path: Path) -> pd.DataFrame:
    """Load CSV with automatic delimiter detection (supporting tab, semicolon, comma).

    Args:
        file_path: Path to CSV file.

    Returns:
        Loaded raw DataFrame.
    """
    delimiters = ["\t", ";", ","]
    for sep in delimiters:
        try:
            df = pd.read_csv(file_path, sep=sep)
            if len(df.columns) > 5 and ("Income" in df.columns or "customer_id" in df.columns):
                return df
        except Exception:
            continue

    # Fallback to python sniffer engine
    return pd.read_csv(file_path, sep=None, engine="python")


def parse_marketing_campaign(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Map raw marketing campaign attributes to Kintsugi borrower schema.

    Transformations:
    - monthly_income = Income (treated directly as monthly income, no division by 12)
    - monthly_expenses = (MntWines + MntFruits + MntMeatProducts + MntFishProducts + MntSweetProducts + MntGoldProds)
    - deal_purchase_ratio = NumDealsPurchases / (NumWebPurchases + NumStorePurchases + NumCatalogPurchases + 0.001)
    - dependents = Kidhome + Teenhome
    - Synthesizes realistic baseline loan parameters:
      remaining_principal = 300,000, current_emi = 14,403.86, remaining_tenure_months = 24, annual_interest_rate = 0.14
    - Calibrates liquid buffers, credit utilization, and borrower identities.

    Args:
        df_raw: Raw DataFrame from marketing_campaign.csv.

    Returns:
        Standardized DataFrame adhering to REQUIRED_COLUMNS.
    """
    df = df_raw.copy()
    needed = ["ID", "Income", "NumDealsPurchases", "NumWebPurchases", "NumStorePurchases", "NumCatalogPurchases"]
    missing = [c for c in needed if c not in df]
    if missing:
        raise ValueError(f"Marketing data is missing columns: {missing}")
    numeric = needed + [c for c in df if c.startswith("Mnt") or c in ("Kidhome", "Teenhome", "Complain")]
    for col in numeric:
        original = df[col]
        df[col] = pd.to_numeric(original, errors="coerce")
        invalid_missing = df[col].isna() & (original.notna() if col == "Income" else True)
        if invalid_missing.any() or np.isinf(df[col]).any() or (df[col].dropna() < 0).any():
            raise ValueError(f"Invalid marketing field: {col}")
    if df["ID"].duplicated().any() or (df["ID"] % 1 != 0).any():
        raise ValueError("Marketing ID must contain unique integers")

    # 1. Impute missing Income with median and compute monthly_income (treated directly as monthly income)
    median_income = float(df["Income"].dropna().median()) if not df["Income"].dropna().empty else 50000.0
    income = df["Income"].fillna(median_income).astype(float)
    monthly_income = np.maximum(income, 100.0)

    # 2. Compute monthly_expenses from Mnt purchase columns
    mnt_cols = [
        "MntWines",
        "MntFruits",
        "MntMeatProducts",
        "MntFishProducts",
        "MntSweetProducts",
        "MntGoldProds",
    ]
    present_mnt = [c for c in mnt_cols if c in df.columns]
    if present_mnt:
        total_spent = df[present_mnt].sum(axis=1).astype(float)
        monthly_expenses = np.maximum(total_spent, 10.0)
    else:
        monthly_expenses = monthly_income * 0.45

    # Compute discretionary_ratio (Wines, Gold, Sweets relative to total spent)
    disc_cols = [c for c in ["MntWines", "MntGoldProds", "MntSweetProducts"] if c in df.columns]
    if disc_cols and present_mnt:
        discretionary_spent = df[disc_cols].sum(axis=1).astype(float)
        discretionary_ratio = np.clip(discretionary_spent / (total_spent + 0.001), 0.0, 1.0)
    else:
        discretionary_ratio = pd.Series([0.55] * len(df))

    # 3. Compute deal_purchase_ratio
    deals = df.get("NumDealsPurchases", pd.Series(0, index=df.index)).astype(float)
    web = df.get("NumWebPurchases", pd.Series(0, index=df.index)).astype(float)
    store = df.get("NumStorePurchases", pd.Series(0, index=df.index)).astype(float)
    catalog = df.get("NumCatalogPurchases", pd.Series(0, index=df.index)).astype(float)
    total_purchases = web + store + catalog + 0.001
    deal_purchase_ratio = np.clip(deals / total_purchases, 0.0, 1.0)

    # 4. Dependents
    kids = df.get("Kidhome", pd.Series(0, index=df.index)).astype(int)
    teens = df.get("Teenhome", pd.Series(0, index=df.index)).astype(int)
    dependents = kids + teens

    # 5. Baseline loan parameters (300k principal, 14.4k EMI, 24 mos tenure, 14% APR)
    remaining_principal = 300000.0
    current_emi = BASELINE_EMI
    remaining_tenure = 24
    annual_rate = 0.14

    # 6. Borrower identities
    first_names = [
        "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Rahul", "Kavita",
        "Siddharth", "Pooja", "Arjun", "Deepika", "Karan", "Sneha", "Aditya", "Meera",
        "Rajesh", "Sunita", "Amit", "Swati", "Suresh", "Divya", "Gaurav", "Shreya"
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Mehta", "Iyer", "Nair", "Reddy", "Rao",
        "Mukherjee", "Chatterjee", "Gupta", "Malhotra", "Kapoor", "Bhat", "Deshmukh", "Singh"
    ]

    n_samples = len(df)
    rng = np.random.RandomState(42)

    ids = df.get("ID", pd.Series(range(1, n_samples + 1))).astype(int).values
    cust_ids = [f"CUST-{val:04d}" for val in ids]
    names = [
        f"{first_names[val % len(first_names)]} {last_names[(val // len(first_names)) % len(last_names)]}"
        for val in ids
    ]
    phones = [f"+91-98{val % 90000000 + 10000000}" for val in ids]

    # 7. Savings buffers, depletion rate, credit utilization, late days
    # Distress behavior: high deal purchases (>0.40) correlates with cashflow strain
    deal_vals = deal_purchase_ratio.to_numpy(dtype=float, copy=True)
    is_strained = deal_vals > 0.40

    buffer_multiplier = np.where(
        is_strained,
        rng.uniform(0.15, 0.85, n_samples),
        rng.uniform(1.5, 4.5, n_samples),
    )
    savings_balance = np.round(current_emi * buffer_multiplier, 2)

    depletion_multiplier = np.where(
        is_strained,
        rng.uniform(1.8, 3.8, n_samples),
        rng.uniform(0.95, 1.15, n_samples),
    )
    prev_savings = np.round(savings_balance * depletion_multiplier, 2)

    credit_util = np.where(
        is_strained,
        rng.uniform(0.70, 0.98, n_samples),
        rng.uniform(0.18, 0.52, n_samples),
    )

    complain = df.get("Complain", pd.Series([0] * n_samples)).to_numpy(copy=True)
    late_days = np.where(
        (deal_vals > 0.50) | (complain == 1),
        rng.choice([5, 12, 18, 25, 35], n_samples),
        rng.choice([0, 0, 0, 1, 2], n_samples),
    )

    records = {
        "customer_id": cust_ids,
        "name": names,
        "phone": phones,
        "monthly_income": np.round(monthly_income.values, 2),
        "monthly_expenses": np.round(monthly_expenses.values, 2),
        "current_emi": current_emi,
        "remaining_principal": remaining_principal,
        "remaining_tenure_months": remaining_tenure,
        "annual_interest_rate": annual_rate,
        "savings_balance": savings_balance,
        "previous_savings_balance": prev_savings,
        "deal_purchase_ratio": np.round(deal_vals, 4),
        "credit_utilization": np.round(credit_util, 4),
        "late_payment_days_last_6m": late_days,
        "dependents": dependents.values,
        "discretionary_ratio": np.round(discretionary_ratio.values, 4),
    }

    # Retain all original raw columns from marketing_campaign.csv
    result_df = df_raw.copy()
    for col, val in records.items():
        result_df[col] = val

    result_df.attrs.update(data_source="marketing_simulation", simulation=True,
                           data_warning="Marketing records with generated identities, loans, savings, utilization and late days; not real borrower accounts.",
                           imputed_income_count=int(df_raw["Income"].isna().sum()))
    return normalize_customers(result_df)


def generate_synthetic_customers(n_samples: int = 300, random_seed: int = 42) -> pd.DataFrame:
    """Generate realistic synthetic customer records containing financial distress patterns.

    Args:
        n_samples: Number of borrower records to generate.
        random_seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic borrower attributes.
    """
    np.random.seed(random_seed)

    first_names = [
        "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Rahul", "Kavita",
        "Siddharth", "Pooja", "Arjun", "Deepika", "Karan", "Sneha", "Aditya", "Meera",
        "Rajesh", "Sunita", "Amit", "Swati", "Suresh", "Divya", "Gaurav", "Shreya"
    ]
    last_names = [
        "Sharma", "Verma", "Patel", "Mehta", "Iyer", "Nair", "Reddy", "Rao",
        "Mukherjee", "Chatterjee", "Gupta", "Malhotra", "Kapoor", "Bhat", "Deshmukh", "Singh"
    ]

    records = []

    for i in range(1, n_samples + 1):
        cust_id = f"CUST-{i:04d}"
        name = f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
        phone = f"+91-98{np.random.randint(10000000, 99999999)}"

        # 75% normal/mild stress, 25% severe/unsupervised distress
        is_stressed = np.random.rand() < 0.22

        if not is_stressed:
            # Healthy to moderate borrower
            monthly_income = float(np.random.normal(75000, 15000))
            monthly_income = max(30000.0, monthly_income)

            spend_ratio = np.random.uniform(0.35, 0.65)
            monthly_expenses = monthly_income * spend_ratio

            emi_ratio = np.random.uniform(0.15, 0.35)
            current_emi = monthly_income * emi_ratio

            remaining_tenure = int(np.random.choice([12, 24, 36, 48, 60]))
            annual_rate = float(np.random.choice([0.105, 0.115, 0.12, 0.13]))

            # Principal approximately derived from EMI & tenure
            r = annual_rate / 12.0
            p = current_emi * ((1 + r)**remaining_tenure - 1) / (r * (1 + r)**remaining_tenure)
            remaining_principal = round(max(50000.0, float(p)), 2)

            savings_balance = float(np.random.uniform(1.5, 6.0) * (monthly_expenses + current_emi))
            previous_savings = savings_balance * np.random.uniform(0.95, 1.15)
            deal_purchase_ratio = float(np.random.beta(2, 6))  # low deal reliance
            credit_utilization = float(np.random.uniform(0.15, 0.55))
            late_days = int(np.random.choice([0, 0, 0, 0, 1, 2]))
            dependents = int(np.random.choice([0, 1, 2]))
        else:
            # Distressed borrower (high expense, sudden savings drop, deal hunting, late payments)
            monthly_income = float(np.random.normal(55000, 12000))
            monthly_income = max(25000.0, monthly_income)

            spend_ratio = np.random.uniform(0.65, 0.95)
            monthly_expenses = monthly_income * spend_ratio

            emi_ratio = np.random.uniform(0.35, 0.55)
            current_emi = monthly_income * emi_ratio

            remaining_tenure = int(np.random.choice([24, 36, 48, 60]))
            annual_rate = float(np.random.choice([0.125, 0.135, 0.145, 0.15]))

            r = annual_rate / 12.0
            p = current_emi * ((1 + r)**remaining_tenure - 1) / (r * (1 + r)**remaining_tenure)
            remaining_principal = round(max(80000.0, float(p)), 2)

            # Rapidly depleting buffer
            savings_balance = float(np.random.uniform(0.1, 0.9) * (monthly_expenses + current_emi))
            previous_savings = savings_balance * np.random.uniform(2.0, 4.5)  # huge drop in savings!
            deal_purchase_ratio = float(np.random.uniform(0.65, 0.92))  # heavy deal/coupon reliance
            credit_utilization = float(np.random.uniform(0.75, 0.98))  # maxed out cards
            late_days = int(np.random.choice([5, 12, 18, 25, 40]))
            dependents = int(np.random.choice([1, 2, 3]))

        current_emi = calculate_emi(remaining_principal, annual_rate, remaining_tenure)
        records.append({
            "customer_id": cust_id,
            "name": name,
            "phone": phone,
            "monthly_income": round(monthly_income, 2),
            "monthly_expenses": round(monthly_expenses, 2),
            "current_emi": round(current_emi, 2),
            "remaining_principal": remaining_principal,
            "remaining_tenure_months": remaining_tenure,
            "annual_interest_rate": annual_rate,
            "savings_balance": round(savings_balance, 2),
            "previous_savings_balance": round(previous_savings, 2),
            "deal_purchase_ratio": round(deal_purchase_ratio, 4),
            "credit_utilization": round(credit_utilization, 4),
            "late_payment_days_last_6m": late_days,
            "dependents": dependents,
            "discretionary_ratio": round(float(spend_ratio * 0.75), 4),
        })

    df = pd.DataFrame(records)
    df.attrs.update(data_source="synthetic_fallback", simulation=True,
                    data_warning=f"Using {n_samples} entirely synthetic demo accounts; no observed borrower finances.")
    return normalize_customers(df)


def load_customer_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """Load customer dataset, prioritizing marketing_campaign.csv.

    Search priority:
    1. Explicit file_path argument if provided.
    2. RAW_DATA_DIR / 'marketing_campaign.csv'
    3. Fallback: generate synthetic customer dataset in memory.

    Args:
        file_path: Optional path to CSV file.

    Returns:
        Standardized DataFrame with customer records.
    """
    target_path: Optional[Path] = None

    if file_path is not None:
        target_path = Path(file_path)
        if not target_path.is_file():
            raise FileNotFoundError(f"Requested customer dataset does not exist: {target_path}")
    else:
        campaign_candidates = [
            RAW_DATA_DIR / "marketing_campaign.csv",
        ]
        for candidate in campaign_candidates:
            if candidate.exists():
                target_path = candidate
                break

    if target_path is None or not target_path.exists():
        return generate_synthetic_customers(n_samples=300, random_seed=42)

    # Ingest CSV handling delimiters
    df_raw = load_raw_delimited_csv(target_path)

    # Check if this is the marketing_campaign.csv format
    if "Income" in df_raw.columns and "NumDealsPurchases" in df_raw.columns:
        df_processed = parse_marketing_campaign(df_raw)
    else:
        df_processed = df_raw

    df_processed = normalize_customers(df_processed)
    df_processed.attrs.setdefault("data_source", "provided_borrower_data")
    df_processed.attrs.setdefault("simulation", False)
    return df_processed
