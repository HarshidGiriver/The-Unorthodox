import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from src.config import BASE_DIR, BANK_NAME
from src.data.loader import load_customer_data
from src.agents.detection_agent import StressDetectionAgent
from web.components.bank_view import render_bank_view
from web.components.customer_view import render_customer_view

# Streamlit Page Setup
st.set_page_config(
    page_title="FinSafe AI | Autonomous Financial Stress & Restructuring Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Injection
css_path = BASE_DIR / "web" / "styles" / "custom.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_and_score_portfolio():
    """Ingest raw portfolio and score distress anomalies using detection agent."""
    df_raw = load_customer_data()
    agent = StressDetectionAgent()
    df_scored = agent.analyze_portfolio(df_raw)
    return df_scored


def main():
    # Top Header
    st.markdown(
        f"""
        <div class="main-header">
            <div>
                <div class="brand-badge">🛡️ FinSafe AI Platform v0.1</div>
                <h1 style="margin: 8px 0 4px 0; color: #ffffff; font-size: 2.2rem;">Autonomous Distress Detection & Debt Restructuring</h1>
                <p style="color: #94a3b8; margin: 0; font-size: 0.95rem;">
                    Proactive non-linear anomaly detection • Deterministic loan amortization • RBI-compliant empathetic outreach
                </p>
            </div>
            <div style="text-align: right;">
                <div class="rbi-badge">✓ RBI Fair Practices Verified</div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 6px;">Enterprise Institution: {BANK_NAME}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### ⚙️ System Controls")
        st.info("Unsupervised Isolation Forest + Deterministic Amortization Solver")

        if st.button("🔄 Refresh / Re-score Portfolio"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("#### 📜 Regulatory Adherence")
        st.caption("• RBI Fair Practices Code for Lenders\n• Non-coercive resolution\n• Transparency in charges\n• Permitted hours: 08:00 - 19:00")

    # Load data
    with st.spinner("Analyzing portfolio risk with Isolation Forest..."):
        df_portfolio = load_and_score_portfolio()

    # Navigation Tabs
    tab_bank, tab_customer, tab_docs = st.tabs([
        "🏦 Underwriter Command Center",
        "📱 Customer Relief Simulator",
        "📑 Architecture & RBI Framework",
    ])

    with tab_bank:
        render_bank_view(df_portfolio)

    with tab_customer:
        render_customer_view(df_portfolio)

    with tab_docs:
        st.markdown("### 📐 System Architecture & Regulatory Compliance Framework")
        st.markdown(
            """
            #### 1. Multi-Agent Autonomous Architecture
            - **Detection Agent**: Ingests non-linear spending metrics (spend-to-income, deal reliance ratio, liquidity runway, savings depletion velocity) and maps them into multidimensional space using an unsupervised **Isolation Forest** model.
            - **Restructuring Agent**: Solves deterministic loan amortization equations preserving mathematical invariance (ensuring sum of principal components matches initial balance, and terminal balance strictly equals 0).
            - **Outreach Agent**: Generates dignified, transparent borrower notices conforming to **RBI Fair Practices Code for Lenders (FPC)**.

            #### 2. Mathematical Amortization Invariance
            The monthly installment is derived from:
            $$EMI = \\frac{P \\cdot r \\cdot (1+r)^n}{(1+r)^n - 1}$$
            Where:
            - $P$ = Outstanding loan principal
            - $r$ = Monthly interest rate ($APR / 12$)
            - $n$ = Repayment tenure in months
            
            Every generated schedule enforces:
            $$\\sum_{t=1}^{n} Principal_t = P, \\quad Balance_n = 0$$

            #### 3. RBI Fair Practices Code Guidelines
            - Strictly forbids aggressive, misleading, or harassing recovery practices.
            - Prohibits contacting borrowers outside permitted calling hours (08:00 to 19:00).
            - Requires transparent disclosure of all financial impacts, including total lifetime interest variance under restructuring.
            - Guarantees immediate access to the Bank's designated Grievance Redressal Officer.
            """
        )


if __name__ == "__main__":
    main()
