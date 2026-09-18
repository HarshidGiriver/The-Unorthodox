"""Unit tests for stress feature calculations."""

import pytest
import pandas as pd
from src.data.feature_engineering import compute_stress_features
from src.data.loader import load_customer_data, load_raw_delimited_csv


def test_feature_calculation_normal_case():
    """Verify basic feature engineering with standard inputs."""
    sample = {
        "monthly_income": 100000.0,
        "monthly_expenses": 40000.0,
        "current_emi": 20000.0,
        "savings_balance": 180000.0,
        "previous_savings_balance": 180000.0,
        "deal_purchase_ratio": 0.2,
        "credit_utilization": 0.3,
        "late_payment_days_last_6m": 0,
    }
    df = compute_stress_features(sample)

    assert len(df) == 1
    assert df["spend_to_income_ratio"].iloc[0] == pytest.approx(0.40, rel=1e-2)
    assert df["emi_burden_ratio"].iloc[0] == pytest.approx(0.20, rel=1e-2)
    assert df["total_outflow_burden"].iloc[0] == pytest.approx(0.60, rel=1e-2)
    assert df["liquidity_runway_months"].iloc[0] == pytest.approx(3.0, rel=1e-2)
    assert 0.0 <= df["stress_index"].iloc[0] <= 100.0


def test_zero_income_and_division_safety():
    """Verify system handles zero income and empty savings without crashing."""
    sample = {
        "monthly_income": 0.0,
        "monthly_expenses": 30000.0,
        "current_emi": 15000.0,
        "savings_balance": 0.0,
        "previous_savings_balance": 0.0,
        "deal_purchase_ratio": 0.85,
        "credit_utilization": 0.95,
        "late_payment_days_last_6m": 15,
    }
    df = compute_stress_features(sample)

    assert not df["spend_to_income_ratio"].isna().any()
    assert not df["liquidity_runway_months"].isna().any()
    assert not df["stress_index"].isna().any()
    assert 0.0 <= df["stress_index"].iloc[0] <= 100.0


def test_stress_index_monotonicity():
    """Verify that a stressed profile receives a significantly higher stress index than a healthy profile."""
    healthy = {
        "monthly_income": 120000.0,
        "monthly_expenses": 40000.0,
        "current_emi": 15000.0,
        "savings_balance": 350000.0,
        "previous_savings_balance": 350000.0,
        "deal_purchase_ratio": 0.1,
        "credit_utilization": 0.2,
        "late_payment_days_last_6m": 0,
    }
    distressed = {
        "monthly_income": 50000.0,
        "monthly_expenses": 45000.0,
        "current_emi": 20000.0,
        "savings_balance": 5000.0,
        "previous_savings_balance": 50000.0,
        "deal_purchase_ratio": 0.9,
        "credit_utilization": 0.95,
        "late_payment_days_last_6m": 30,
    }

    df_h = compute_stress_features(healthy)
    df_d = compute_stress_features(distressed)

    assert df_d["stress_index"].iloc[0] > df_h["stress_index"].iloc[0]
    assert df_d["liquidity_runway_months"].iloc[0] < df_h["liquidity_runway_months"].iloc[0]
    assert df_d["total_outflow_burden"].iloc[0] > 1.0


def test_marketing_campaign_loading_and_mapping():
    """Verify that marketing_campaign.csv loads with 2,240 rows and properly maps attributes."""
    df = load_customer_data()
    assert len(df) == 2240
    assert "dependents" in df.columns
    assert "deal_purchase_ratio" in df.columns
    assert df["monthly_income"].isna().sum() == 0
    assert (df["remaining_principal"] == 300000.0).all()
    assert (df["current_emi"] == 14400.0).all()
    assert (df["remaining_tenure_months"] == 24).all()
    assert (df["annual_interest_rate"] == 0.14).all()

    feat_df = compute_stress_features(df)
    assert len(feat_df) == 2240
    assert feat_df["stress_index"].isna().sum() == 0


def test_triage_queue_records_match_the_source_dataset():
    """Every dashboard customer is traceable to the corresponding CSV record."""
    from pathlib import Path

    raw = load_raw_delimited_csv(Path("data/raw/marketing_campaign.csv"))
    portfolio = load_customer_data()

    assert len(portfolio) == len(raw) == 2240
    assert portfolio["customer_id"].str.removeprefix("CUST-").astype(int).tolist() == raw["ID"].astype(int).tolist()

    expected_monthly_income = (raw["Income"].fillna(raw["Income"].median()) / 12).round(2)
    assert portfolio["monthly_income"].tolist() == expected_monthly_income.tolist()

    total_purchases = raw["NumWebPurchases"] + raw["NumStorePurchases"] + raw["NumCatalogPurchases"] + 0.001
    expected_deal_index = (raw["NumDealsPurchases"] / total_purchases).clip(0, 1).round(4)
    assert portfolio["deal_purchase_ratio"].tolist() == expected_deal_index.tolist()
