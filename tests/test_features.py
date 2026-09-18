"""Unit tests for stress feature calculations."""

import pytest
import pandas as pd
from src.data.feature_engineering import compute_stress_features


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
