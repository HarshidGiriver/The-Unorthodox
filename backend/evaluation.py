"""Held-out anomaly evaluation; outcome metrics only when observed labels exist."""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

from backend.config import FEATURE_COLUMNS, FEATURE_SCHEMA_VERSION

FEATURE_VERSION = FEATURE_SCHEMA_VERSION


def evaluate(features):
    if len(features) < 10:
        raise ValueError("At least 10 records are required for held-out evaluation")
    indices = np.arange(len(features))
    if "snapshot_date" in features:
        dates = pd.to_datetime(features["snapshot_date"], errors="raise", utc=True)
        cutoff = dates.sort_values().iloc[int(len(dates) * .7)]
        train, test = indices[(dates < cutoff).to_numpy()], indices[(dates >= cutoff).to_numpy()]
        if not len(train) or not len(test):
            raise ValueError("Temporal evaluation requires distinct training and holdout dates")
        strategy = "temporal snapshot_date; equal dates stay in the same partition"
    else:
        train, test = train_test_split(indices, test_size=.3, random_state=42)
        strategy = "seeded random 70/30; descriptive demo evaluation, not prospective validation"
    x = features[FEATURE_COLUMNS].to_numpy()
    scaler = RobustScaler().fit(x[train])
    model = IsolationForest(n_estimators=150, contamination=.15, random_state=42, n_jobs=-1)
    model.fit(scaler.transform(x[train]))
    transformed = scaler.transform(x[test])
    predictions = model.predict(transformed) == -1
    rules = features.iloc[test]["stress_index"].to_numpy() >= 65
    result = {"split": strategy, "train_rows": len(train), "holdout_rows": len(test),
              "isolation_forest_anomaly_rate": float(predictions.mean()), "rules_anomaly_rate": float(rules.mean()),
              "agreement": float((predictions == rules).mean()),
              "outcome_metrics": None,
              "limitations": "Anomaly separation is not proof of default prediction. Demo finance fields are generated."}
    if "observed_default" in features:
        if features.attrs.get("simulation"):
            raise ValueError("Outcome metrics require observed borrower data, not simulation records")
        labels = pd.to_numeric(features["observed_default"], errors="raise")
        if labels.isna().any() or not labels.isin([0, 1]).all():
            raise ValueError("observed_default must contain complete observed 0/1 outcomes")
        y = labels.iloc[test].to_numpy()
        outcomes = {}
        for name, prediction, score in (
            ("isolation_forest", predictions, -model.decision_function(transformed)),
            ("rules", rules, features.iloc[test]["stress_index"].to_numpy()),
        ):
            precision, recall, f1, _ = precision_recall_fscore_support(y, prediction, average="binary", zero_division=0)
            outcomes[name] = {"precision": float(precision), "recall": float(recall), "f1": float(f1),
                              "roc_auc": float(roc_auc_score(y, score)) if len(set(y)) == 2 else None}
        result["outcome_metrics"] = outcomes
        result["limitations"] = "Verify label horizon, temporal leakage and cohort representativeness before interpreting outcomes."
    return result
