"""Data ingestion, schema validation, and synthetic data generation for FinSafe AI."""

from typing import Tuple, List, Optional
from pathlib import Path
import numpy as np
import pandas as pd
from src.config import RAW_DATA_DIR

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
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return len(missing) == 0, missing


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
        })

    df = pd.DataFrame(records)
    return df


def load_customer_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """Load customer CSV data or generate and persist synthetic data if file does not exist.

    Args:
        file_path: Optional path to CSV file. Defaults to data/raw/customers_sample.csv.

    Returns:
        Loaded DataFrame.
    """
    if file_path is None:
        target_path = RAW_DATA_DIR / "customers_sample.csv"
    else:
        target_path = Path(file_path)

    if not target_path.exists():
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        df = generate_synthetic_customers(n_samples=300, random_seed=42)
        df.to_csv(target_path, index=False)
        return df

    df = pd.read_csv(target_path)
    is_valid, missing = validate_schema(df)
    if not is_valid:
        raise ValueError(f"CSV is missing required schema columns: {missing}")

    return df
