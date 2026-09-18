"""Unit tests for loan restructuring mathematical invariance."""

import pytest
from src.agents.restructuring_agent import DebtRestructuringAgent


def test_emi_calculation_formula():
    """Verify EMI against standard closed-form financial math."""
    agent = DebtRestructuringAgent()
    # P = 100,000, r = 12% APR (1% per month), n = 12 months
    # Formula: 100000 * 0.01 * (1.01)^12 / ((1.01)^12 - 1) ≈ 8884.88
    emi = agent.calculate_emi(100000.0, 0.12, 12)
    assert emi == pytest.approx(8884.88, abs=0.1)


def test_amortization_mathematical_invariance():
    """Verify principal conservation and terminal zero balance."""
    agent = DebtRestructuringAgent()
    principal = 250000.0
    rate = 0.115
    tenure = 36

    schedule = agent.generate_amortization_schedule(principal, rate, tenure)

    assert len(schedule) == tenure
    total_principal_paid = schedule["principal_paid"].sum()
    assert total_principal_paid == pytest.approx(principal, abs=0.05)
    assert schedule["ending_balance"].iloc[-1] == 0.0


def test_tenure_extension_reduces_emi():
    """Verify that extending tenure strictly decreases monthly required payment."""
    agent = DebtRestructuringAgent()
    p = 300000.0
    r = 0.13
    emi_24 = agent.calculate_emi(p, r, 24)
    emi_36 = agent.calculate_emi(p, r, 36)
    emi_48 = agent.calculate_emi(p, r, 48)

    assert emi_24 > emi_36 > emi_48


def test_moratorium_principal_freeze():
    """Verify that during moratorium months, principal paid is zero."""
    agent = DebtRestructuringAgent()
    principal = 150000.0
    rate = 0.12
    tenure = 24
    moratorium = 3

    schedule = agent.generate_amortization_schedule(principal, rate, tenure, moratorium_months=moratorium)

    for m in range(moratorium):
        assert schedule["principal_paid"].iloc[m] == 0.0
        assert bool(schedule["is_moratorium"].iloc[m]) is True

    # Total principal paid across full tenure must still equal original principal
    assert schedule["principal_paid"].sum() == pytest.approx(principal, abs=0.05)
    assert schedule["ending_balance"].iloc[-1] == 0.0
