"""Stress Detection Agent: Unsupervised stress anomaly scoring and risk tier categorization."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from src.config import (
    ISOLATION_FOREST_PATH,
    SCALER_PATH,
    FEATURE_COLUMNS,
    TIER_1_LOW_RISK_MAX,
    TIER_2_MODERATE_STRESS_MAX,
)
from src.data.feature_engineering import compute_stress_features, get_feature_matrix


class StressDetectionAgent:
    """Agent responsible for identifying early, non-linear borrower distress anomalies."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        scaler_path: Optional[Path] = None,
    ):
        self.model_path = model_path or ISOLATION_FOREST_PATH
        self.scaler_path = scaler_path or SCALER_PATH
        self.model = None
        self.scaler = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        """Load trained Isolation Forest and Scaler if available."""
        if self.scaler_path.exists() and self.model_path.exists():
            try:
                self.scaler = joblib.load(self.scaler_path)
                self.model = joblib.load(self.model_path)
            except Exception as e:
                print(f"Warning: Could not load trained models from disk ({e}). Fallback to heuristic scoring.")
                self.scaler = None
                self.model = None

    def analyze_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze entire customer portfolio, appending risk scores and tiers.

        Args:
            df: DataFrame of customer records (with or without engineered features).

        Returns:
            Enriched DataFrame with anomaly scores, risk tiers, and primary drivers.
        """
        # Ensure features are computed
        if "stress_index" not in df.columns:
            df_proc = compute_stress_features(df)
        else:
            df_proc = df.copy()

        scores = []
        is_anomaly_list = []
        risk_tiers = []
        primary_drivers = []

        for _, row in df_proc.iterrows():
            result = self.score_customer(row)
            scores.append(result["anomaly_score"])
            is_anomaly_list.append(result["is_anomaly"])
            risk_tiers.append(result["risk_tier"])
            primary_drivers.append(", ".join(result["top_risk_factors"]))

        df_proc["anomaly_score"] = scores
        df_proc["is_anomaly"] = is_anomaly_list
        df_proc["risk_tier"] = risk_tiers
        df_proc["primary_drivers"] = primary_drivers

        return df_proc

    def score_customer(self, customer_data: pd.Series) -> Dict[str, Any]:
        """Score an individual customer profile.

        Args:
            customer_data: Series or dictionary containing customer attributes.

        Returns:
            Dictionary containing anomaly score, flag, risk tier, and top factors.
        """
        if self.model is not None and self.scaler is not None:
            features = [float(customer_data[col]) for col in FEATURE_COLUMNS]
            X = np.array([features])
            X_scaled = self.scaler.transform(X)

            # IsolationForest decision_function: lower means more abnormal
            # Raw score is typically in [-0.5, 0.5]
            raw_dec = float(self.model.decision_function(X_scaled)[0])
            pred = int(self.model.predict(X_scaled)[0])  # -1 for anomaly, 1 for normal
            is_anomaly = bool(pred == -1)

            # Calibrate raw decision score into intuitive [0, 1] distress scale:
            if is_anomaly:
                # Severe distress anomalies: 0.65 to 1.0 (Tier 3)
                anomaly_score = float(np.clip(0.65 + (abs(raw_dec) * 2.5), 0.65, 1.0))
            else:
                # Normal / moderate profiles: 0.0 to 0.65
                # Higher raw_dec means more typical/healthy
                norm_factor = max(0.0, 1.0 - (raw_dec / 0.14))
                anomaly_score = float(np.clip(norm_factor * 0.64, 0.05, 0.64))
        else:
            # Heuristic fallback using engineered stress_index
            stress_idx = float(customer_data.get("stress_index", 30.0))
            anomaly_score = float(np.clip(stress_idx / 100.0, 0.0, 1.0))
            is_anomaly = anomaly_score >= 0.55

        # Determine Risk Tier
        if anomaly_score < TIER_1_LOW_RISK_MAX:
            risk_tier = "Tier 1 (Normal / Low Risk)"
        elif anomaly_score < TIER_2_MODERATE_STRESS_MAX:
            risk_tier = "Tier 2 (Moderate Stress)"
        else:
            risk_tier = "Tier 3 (High Anomaly / Severe Distress)"

        top_factors = self._extract_risk_factors(customer_data)

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "risk_tier": risk_tier,
            "top_risk_factors": top_factors,
        }

    def _extract_risk_factors(self, row: pd.Series) -> List[str]:
        """Extract top human-readable factors contributing to borrower stress."""
        factors = []

        total_burden = float(row.get("total_outflow_burden", 0.0))
        runway = float(row.get("liquidity_runway_months", 5.0))
        depletion = float(row.get("savings_depletion_rate", 0.0))
        deal_idx = float(row.get("deal_reliance_index", 0.0))
        late_days = float(row.get("late_payment_days_last_6m", 0.0))
        credit_util = float(row.get("credit_utilization_ratio", 0.0))

        if total_burden > 0.90:
            pct = int(total_burden * 100)
            factors.append(f"High Outflow Burden ({pct}% of income)")
        if runway < 1.5:
            factors.append(f"Low Liquidity Runway ({runway:.1f} months)")
        if depletion > 0.30:
            factors.append(f"Rapid Savings Burn ({int(depletion*100)}% depletion)")
        if deal_idx > 0.60:
            factors.append(f"Elevated Deal Reliance ({int(deal_idx*100)}%)")
        if late_days > 0:
            factors.append(f"Recent Payment Friction ({int(late_days)} late days)")
        if credit_util > 0.80:
            factors.append(f"High Credit Card Utilization ({int(credit_util*100)}%)")

        if not factors:
            factors.append("Stable Cashflow Profile")

        return factors[:3]
