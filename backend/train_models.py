import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from backend.config import MODELS_DIR, ISOLATION_FOREST_PATH, SCALER_PATH, FEATURE_COLUMNS
from backend.data.loader import load_customer_data
from backend.data.feature_engineering import compute_stress_features, get_feature_matrix


def train_and_save_models():
    """Train unsupervised stress anomaly model on customer dataset and save scaler and model artifacts."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading customer dataset for training (marketing_campaign.csv)...")
    df_raw = load_customer_data()
    print(f"Loaded {len(df_raw)} borrower profiles.")

    print("Computing stress features...")
    df_features = compute_stress_features(df_raw)
    X = get_feature_matrix(df_features)

    print(f"Fitting RobustScaler on {X.shape[0]} samples with {X.shape[1]} features...")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    print("Fitting IsolationForest (n_estimators=150, contamination=0.15)...")
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.15,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    iso_forest.fit(X_scaled)

    # Save artifacts
    print(f"Saving scaler to {SCALER_PATH}...")
    joblib.dump(scaler, SCALER_PATH)

    print(f"Saving isolation forest to {ISOLATION_FOREST_PATH}...")
    joblib.dump(iso_forest, ISOLATION_FOREST_PATH)

    print("Model training and serialization completed successfully!")
    return iso_forest, scaler


if __name__ == "__main__":
    train_and_save_models()
