import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from src.config import MODELS_DIR, ISOLATION_FOREST_PATH, SCALER_PATH, FEATURE_COLUMNS
from src.data.loader import generate_synthetic_customers
from src.data.feature_engineering import compute_stress_features, get_feature_matrix


def train_and_save_models():
    """Train unsupervised stress anomaly model and save scaler and model artifacts."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic training dataset...")
    df_raw = generate_synthetic_customers(n_samples=500, random_seed=42)
    df_features = compute_stress_features(df_raw)
    X = get_feature_matrix(df_features)

    print(f"Fitting RobustScaler on {X.shape[0]} samples with {X.shape[1]} features...")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    print("Fitting IsolationForest (contamination=0.15)...")
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
