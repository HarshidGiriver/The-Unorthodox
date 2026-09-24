import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from backend.config import MODELS_DIR, ISOLATION_FOREST_PATH, SCALER_PATH, FEATURE_COLUMNS
from backend.evaluation import evaluate, FEATURE_VERSION
from backend.data.loader import load_customer_data
from backend.data.feature_engineering import compute_stress_features, get_feature_matrix


def train_and_save_models(file_path=None):
    """Train unsupervised stress anomaly model on customer dataset and save scaler and model artifacts."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading customer dataset for training (marketing_campaign.csv)...")
    df_raw = load_customer_data(file_path)
    print(f"Loaded {len(df_raw)} borrower profiles.")

    print("Computing stress features...")
    df_features = compute_stress_features(df_raw)
    evaluation = evaluate(df_features)
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
    SCALER_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)

    print(f"Saving isolation forest to {ISOLATION_FOREST_PATH}...")
    ISOLATION_FOREST_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(iso_forest, ISOLATION_FOREST_PATH)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    from backend.config import RAW_DATA_DIR
    source_path = Path(file_path) if file_path else RAW_DATA_DIR / "marketing_campaign.csv"
    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
        "dependencies": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "joblib")},
        "feature_version": FEATURE_VERSION, "features": FEATURE_COLUMNS,
        "dataset_sha256": digest(source_path) if source_path.exists() else None,
        "feature_matrix_sha256": hashlib.sha256(X.tobytes()).hexdigest(),
        "model_sha256": digest(ISOLATION_FOREST_PATH), "scaler_sha256": digest(SCALER_PATH),
        "training_rows": len(df_features), "data_source": df_raw.attrs.get("data_source"),
        "evaluation": evaluation,
        "final_model": "Refitted on the complete dataset after separate holdout evaluation",
    }
    ISOLATION_FOREST_PATH.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("Model training and serialization completed successfully!")
    return iso_forest, scaler


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Kintsugi anomaly artifacts with separate holdout evaluation")
    parser.add_argument("--data", help="Validated borrower CSV; optional snapshot_date and observed_default columns")
    args = parser.parse_args()
    train_and_save_models(args.data)
