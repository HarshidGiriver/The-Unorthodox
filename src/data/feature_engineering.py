"""Feature engineering module for calculating financial distress indicators."""

from typing import Union
import numpy as np
import pandas as pd
from src.config import FEATURE_COLUMNS

EPSILON = 1e-5


def compute_stress_features(data: Union[pd.DataFrame, dict, pd.Series]) -> pd.DataFrame:
    """Engineer key financial distress features from raw borrower records.

    Calculates:
    - spend_to_income_ratio: Essential expenditure burden.
    - emi_burden_ratio: Total debt servicing commitments relative to income.
    - total_outflow_burden: Total outflow (expenses + EMI) relative to income.
    - deal_reliance_index: High reliance on emergency deals & coupons.
    - liquidity_runway_months: Months of runway remaining in liquid savings.
    - savings_depletion_rate: Velocity of liquid reserve burn rate.
    - credit_utilization_ratio: Revolving credit limit utilization.
    - stress_index: Calibrated composite index scaled between 0.0 and 100.0.

    Args:
        data: Input DataFrame, Series, or dictionary of customer records.

    Returns:
        DataFrame containing original attributes plus engineered features.
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, pd.Series):
        df = pd.DataFrame([data.to_dict()])
    else:
        df = data.copy()

    # Pre-mapping convenience if raw marketing campaign columns are supplied directly
    if "monthly_income" not in df.columns and "Income" in df.columns:
        med = float(df["Income"].dropna().median()) if not df["Income"].dropna().empty else 50000.0
        df["monthly_income"] = np.maximum(df["Income"].fillna(med).astype(float), 100.0)

    mnt_cols = ["MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts", "MntSweetProducts", "MntGoldProds"]
    if "monthly_expenses" not in df.columns and any(c in df.columns for c in mnt_cols):
        present_mnt = [c for c in mnt_cols if c in df.columns]
        df["monthly_expenses"] = df[present_mnt].sum(axis=1).astype(float)

    if "deal_purchase_ratio" not in df.columns and "NumDealsPurchases" in df.columns:
        deals = df.get("NumDealsPurchases", 0).astype(float)
        web = df.get("NumWebPurchases", 0).astype(float)
        store = df.get("NumStorePurchases", 0).astype(float)
        catalog = df.get("NumCatalogPurchases", 0).astype(float)
        total_p = web + store + catalog + 0.001
        df["deal_purchase_ratio"] = np.clip(deals / total_p, 0.0, 1.0)

    if "dependents" not in df.columns and ("Kidhome" in df.columns or "Teenhome" in df.columns):
        df["dependents"] = df.get("Kidhome", 0).astype(int) + df.get("Teenhome", 0).astype(int)

    # Defaults for missing baseline loan servicing if raw data was provided
    if "current_emi" not in df.columns:
        df["current_emi"] = 14400.0
    if "remaining_principal" not in df.columns:
        df["remaining_principal"] = 300000.0
    if "remaining_tenure_months" not in df.columns:
        df["remaining_tenure_months"] = 24
    if "annual_interest_rate" not in df.columns:
        df["annual_interest_rate"] = 0.14
    if "savings_balance" not in df.columns:
        df["savings_balance"] = 14400.0 * 2.5
    if "previous_savings_balance" not in df.columns:
        df["previous_savings_balance"] = df["savings_balance"]
    if "credit_utilization" not in df.columns:
        df["credit_utilization"] = 0.35
    if "late_payment_days_last_6m" not in df.columns:
        df["late_payment_days_last_6m"] = 0

    # Safe conversion to float
    income = np.maximum(df["monthly_income"].astype(float).values, EPSILON)
    expenses = np.maximum(df["monthly_expenses"].astype(float).values, 0.0)
    emi = np.maximum(df["current_emi"].astype(float).values, 0.0)
    savings = np.maximum(df["savings_balance"].astype(float).values, 0.0)
    prev_savings = np.maximum(df["previous_savings_balance"].astype(float).values, EPSILON)
    deal_ratio = np.clip(df["deal_purchase_ratio"].astype(float).values, 0.0, 1.0)
    credit_util = np.clip(df["credit_utilization"].astype(float).values, 0.0, 2.0)
    late_days = np.maximum(df["late_payment_days_last_6m"].astype(float).values, 0.0)

    # Calculate individual indicators
    spend_to_income = expenses / income
    emi_burden = emi / income
    total_outflow = expenses + emi
    total_outflow_burden = total_outflow / income

    liquidity_runway = savings / (total_outflow + EPSILON)
    # Savings depletion: positive when savings decreased
    depletion_rate = (prev_savings - savings) / prev_savings
    depletion_rate = np.clip(depletion_rate, -1.0, 1.0)

    # Heuristic stress index (0 to 100)
    # 1. Outflow burden contribution (up to 30 pts)
    burden_score = np.clip((total_outflow_burden - 0.5) * 60.0, 0.0, 30.0)

    # 2. Liquidity runway contribution (up to 25 pts)
    runway_score = np.clip((3.0 - liquidity_runway) * (25.0 / 3.0), 0.0, 25.0)

    # 3. Savings depletion contribution (up to 15 pts)
    depletion_score = np.clip(depletion_rate * 20.0, 0.0, 15.0)

    # 4. Deal reliance contribution (up to 15 pts)
    deal_score = np.clip((deal_ratio - 0.3) * 25.0, 0.0, 15.0)

    # 5. Late payments friction (up to 15 pts)
    late_score = np.clip(late_days * 0.75, 0.0, 15.0)

    composite_stress = burden_score + runway_score + depletion_score + deal_score + late_score
    composite_stress = np.clip(composite_stress, 0.0, 100.0)

    # Assign columns
    df["spend_to_income_ratio"] = np.round(spend_to_income, 4)
    df["emi_burden_ratio"] = np.round(emi_burden, 4)
    df["total_outflow_burden"] = np.round(total_outflow_burden, 4)
    df["deal_reliance_index"] = np.round(deal_ratio, 4)
    df["liquidity_runway_months"] = np.round(liquidity_runway, 2)
    df["savings_depletion_rate"] = np.round(depletion_rate, 4)
    df["credit_utilization_ratio"] = np.round(credit_util, 4)
    df["stress_index"] = np.round(composite_stress, 2)
    if "discretionary_ratio" not in df.columns:
        df["discretionary_ratio"] = np.round(np.clip(spend_to_income * 0.75, 0.0, 1.0), 4)
    else:
        df["discretionary_ratio"] = np.round(df["discretionary_ratio"].astype(float), 4)

    return df


def get_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Extract standard feature matrix for machine learning model ingestion.

    Args:
        df: DataFrame containing engineered stress features.

    Returns:
        2D numpy array of features in standard column order.
    """
    return df[FEATURE_COLUMNS].values
