"""Shared application services for the Streamlit frontend.

Keep Streamlit caching and rendering in the frontend so these services can also
be called from scripts and tests.
"""

from backend.agents.detection_agent import StressDetectionAgent
from backend.agents.restructuring_agent import DebtRestructuringAgent
from backend.agents.outreach_agent import EmpatheticOutreachAgent
from backend.data.loader import load_customer_data
from backend.utils.metrics import calculate_portfolio_kpis

__all__ = [
    "load_and_score_portfolio",
    "DebtRestructuringAgent",
    "EmpatheticOutreachAgent",
    "calculate_portfolio_kpis",
]


def load_and_score_portfolio():
    """Load the configured customer data and calculate portfolio distress scores."""
    return StressDetectionAgent().analyze_portfolio(load_customer_data())
