"""Configuration and constants for FinSafe AI."""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables if .env exists
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

# Default Model file paths
ISOLATION_FOREST_PATH = Path(os.getenv("ISOLATION_FOREST_MODEL_PATH", MODELS_DIR / "isolation_forest.joblib"))
SCALER_PATH = Path(os.getenv("SCALER_MODEL_PATH", MODELS_DIR / "scaler.joblib"))

# LLM Configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.2"))

# RBI Regulatory Compliance Constants
RBI_CALL_HOURS_START = os.getenv("RBI_CALL_HOURS_START", "08:00")
RBI_CALL_HOURS_END = os.getenv("RBI_CALL_HOURS_END", "19:00")
BANK_NAME = os.getenv("BANK_NAME", "FinSafe Commercial Bank Ltd.")
BANK_GRIEVANCE_OFFICER_NAME = os.getenv("BANK_GRIEVANCE_OFFICER_NAME", "Aditi Sharma")
BANK_GRIEVANCE_OFFICER_EMAIL = os.getenv("BANK_GRIEVANCE_OFFICER_EMAIL", "grievance@finsafe-bank.in")
BANK_GRIEVANCE_OFFICER_PHONE = os.getenv("BANK_GRIEVANCE_OFFICER_PHONE", "+91-1800-425-0099")

# Feature Constants
FEATURE_COLUMNS = [
    "spend_to_income_ratio",
    "emi_burden_ratio",
    "deal_reliance_index",
    "liquidity_runway_months",
    "savings_depletion_rate",
    "credit_utilization_ratio",
    "late_payment_days_last_6m",
]

# Risk Tier Thresholds
TIER_1_LOW_RISK_MAX = 0.35
TIER_2_MODERATE_STRESS_MAX = 0.65

# Restructuring Constraints
MAX_TENURE_EXTENSION_MONTHS = 36
MIN_TENURE_EXTENSION_MONTHS = 0
MAX_RATE_CONCESSION_BPS = 200  # 2.0%
MAX_MORATORIUM_MONTHS = 6
MIN_MORATORIUM_MONTHS = 0
DEFAULT_ANNUAL_INTEREST_RATE = 0.12  # 12% APR
