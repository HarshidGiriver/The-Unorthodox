"""Regression checks for arithmetic, schema validation and visible fallback modes."""

from pathlib import Path
import numpy as np
import pytest

from backend.agents.restructuring_agent import DebtRestructuringAgent
from backend.agents.detection_agent import StressDetectionAgent
from backend.data.loader import load_customer_data, normalize_customers
from backend.finance import BASELINE_EMI


def test_auto_solver_includes_interest_only_months():
    plan = DebtRestructuringAgent().optimize_restructuring(300000, BASELINE_EMI, 24, .14, moratorium_months=6)
    assert plan["target_met"]
    assert plan["new_emi"] <= BASELINE_EMI * .75
    assert plan["amortization_schedule"].ending_balance.iloc[-1] == 0


def test_unreachable_target_is_reported():
    plan = DebtRestructuringAgent().optimize_restructuring(300000, BASELINE_EMI, 24, .14, target_emi_reduction_pct=.99)
    assert not plan["target_met"]


@pytest.mark.parametrize("parameters", [
    {"moratorium_months": -1}, {"moratorium_months": 7}, {"tenure_extension_months": -2},
    {"rate_concession_bps": -5}, {"rate_concession_bps": 201}, {"target_emi_reduction_pct": float("nan")},
])
def test_restructuring_rejects_invalid_inputs(parameters):
    with pytest.raises(ValueError):
        DebtRestructuringAgent().optimize_restructuring(300000, BASELINE_EMI, 24, .14, **parameters)


def test_moratorium_requires_active_repayments():
    with pytest.raises(ValueError):
        DebtRestructuringAgent().generate_amortization_schedule(300000, .14, 6, 6)


def test_concession_never_increases_low_interest_rate():
    plan = DebtRestructuringAgent().optimize_restructuring(300000, 14000, 24, .03)
    assert plan["new_annual_rate"] == .03


@pytest.mark.parametrize("column,value", [
    ("monthly_income", np.nan), ("monthly_expenses", "invalid"), ("remaining_principal", -1),
    ("annual_interest_rate", 14), ("remaining_tenure_months", 2.5), ("current_emi", np.inf),
])
def test_invalid_borrower_data_rejected(column, value):
    frame = load_customer_data().head(2).copy()
    frame[column] = value
    with pytest.raises(ValueError):
        normalize_customers(frame)


def test_duplicate_ids_and_missing_explicit_file_rejected(tmp_path):
    frame = load_customer_data().head(2).copy()
    frame["customer_id"] = "duplicate"
    with pytest.raises(ValueError):
        normalize_customers(frame)
    with pytest.raises(FileNotFoundError):
        load_customer_data(str(tmp_path / "absent.csv"))


def test_fallback_modes_are_carried_to_ui(monkeypatch, tmp_path):
    monkeypatch.setattr("backend.data.loader.RAW_DATA_DIR", tmp_path)
    frame = load_customer_data()
    scored = StressDetectionAgent(tmp_path / "missing.joblib", tmp_path / "scaler.joblib").analyze_portfolio(frame)
    assert scored.attrs["data_source"] == "synthetic_fallback"
    assert scored.attrs["scoring_mode"] == "heuristic"
    assert scored.attrs["scoring_warning"]
    assert (scored.is_anomaly == scored.risk_tier.str.startswith("Tier 3")).all()


def test_search_metacharacters_and_simulation_labels():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).parents[1] / "frontend" / "app.py"), default_timeout=40).run()
    app.text_input(key="triage_local_search").set_value("[").run()
    assert not app.exception
    assert any("demonstration" in item.value.lower() for item in app.warning)
