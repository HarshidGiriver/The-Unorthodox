import pytest

from backend.data.loader import load_customer_data
from backend.data.feature_engineering import compute_stress_features
from backend.evaluation import evaluate


def test_demo_evaluation_does_not_invent_outcome_accuracy():
    frame = compute_stress_features(load_customer_data().head(30))
    metrics = evaluate(frame)
    assert metrics["train_rows"] + metrics["holdout_rows"] == 30
    assert metrics["outcome_metrics"] is None


def test_temporal_holdout_and_observed_labels():
    frame = compute_stress_features(load_customer_data().head(30))
    frame.attrs["simulation"] = False
    frame["snapshot_date"] = [f"2026-01-{i + 1:02}" for i in range(30)]
    frame["observed_default"] = [i % 2 for i in range(30)]
    metrics = evaluate(frame)
    assert metrics["split"].startswith("temporal")
    assert "rules" in metrics["outcome_metrics"]
    frame["snapshot_date"] = "2026-01-01"
    with pytest.raises(ValueError):
        evaluate(frame)
