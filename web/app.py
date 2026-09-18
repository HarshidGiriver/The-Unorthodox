"""Kintsugi AI: Autonomous Financial Distress Detection & Debt Restructuring Engine.

Visual Identity: Kintsugi - Connect • Assess • Empower
Aesthetic: Tranquil Washi Paper, Mild Glassmorphism (75% Opaque),
           Imperial Pine Jade & Radiant Molten Gold.
High Contrast & 100% English Typography.
"""

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
    page_title="KINTSUGI AI | Connect • Assess • Empower",
    page_icon="🪙",
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
    # 1. Sidebar Brand & Controls
    with st.sidebar:
        # Display Kintsugi Logo
        logo_path = BASE_DIR / "assets" / "kintsugi_logo_thumb.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "assets" / "kintsugi_logo.jpg"

        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)

        st.markdown(
            """
            <div style="text-align: center; margin-top: -8px; margin-bottom: 16px;">
                <div style="font-size: 0.78rem; font-weight: 800; letter-spacing: 0.16em; color: #664614; text-transform: uppercase;">
                    Connect • Assess • Empower
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ System Controls")
        st.info("Unsupervised Isolation Forest + Deterministic Amortization Solver")

        if st.button("🔄 Refresh / Re-score Portfolio", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # Kintsugi Philosophy Callout (English Only)
        st.markdown(
            """
            <div class="kintsugi-callout" style="padding: 14px 16px; margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <span class="seal-badge">KINTSUGI</span>
                    <strong style="font-family: 'Cinzel', serif; font-size: 0.88rem; color: #08201A;">The Philosophy</strong>
                </div>
                <div style="font-size: 0.82rem; color: #12211C; font-weight: 600; line-height: 1.5;">
                    The ancient art of repairing ceramics with gold lacquer. Financial hardship is treated not as a failure to hide, but as an opportunity to restore credit health with dignity.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📜 Regulatory Adherence")
        st.caption(
            "• RBI Fair Practices Code for Lenders\n"
            "• Non-coercive debt resolution\n"
            "• Complete transparency in charges & APR\n"
            "• Permitted outreach hours: 08:00 - 19:00\n"
            "• Statutory Grievance Redressal access"
        )

        st.markdown("---")
        # Generic Executive Profile Footer (No personal name)
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; padding: 6px 0;">
                <div class="kintsugi-avatar">RO</div>
                <div>
                    <div style="font-size: 0.88rem; font-weight: 800; color: #08201A;">Risk Operations Command</div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #664614;">Enterprise Lead Underwriter</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Top Navigation Header (Mild Glassmorphism, English Only, High Contrast)
    st.markdown(
        f"""
        <div class="kintsugi-top-nav">
            <div class="kintsugi-search-bar">
                <span>🔍</span>
                <span style="color: #12211C; font-weight: 600;">Search borrower accounts, principal balance, or distress drivers...</span>
            </div>
            <div class="kintsugi-user-pill">
                <div class="rbi-badge">✓ RBI Fair Practices Verified</div>
                <div style="font-size: 0.82rem; font-weight: 700; color: #0A2B24; border-left: 1px solid #C5A880; padding-left: 12px;">
                    Enterprise: {BANK_NAME}
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="kintsugi-avatar">RO</div>
                    <div style="font-size: 0.84rem; font-weight: 700; color: #08201A;">Underwriter Session Active</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. Kintsugi Hero Banner (Mild Glassmorphism, High Contrast, English Only)
    st.markdown(
        """
        <div class="kintsugi-hero-banner">
            <div class="kintsugi-hero-content">
                <div class="kintsugi-greeting-tag">
                    <span class="brand-badge" style="font-size: 0.72rem; padding: 3px 10px;">Enterprise Risk Engine v1.0</span>
                    <span style="font-weight: 800; color: #664614;">Autonomous Resolution</span>
                </div>
                <h1 class="kintsugi-hero-title">Build your financial tomorrow.</h1>
                <p class="kintsugi-hero-subtitle">
                    Better insights. Smarter decisions. A stronger you.<br>
                    Proactive non-linear anomaly detection • Deterministic loan amortization • Dignified relief
                </p>
                <a href="#underwriter-command-center" class="kintsugi-btn-primary">
                    View Portfolio Triage →
                </a>
            </div>
            <div class="kintsugi-slogan-vertical">
                REBUILD STRONGER • EMPOWER FUTURE
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Quick Action Pills Bar (English Only)
    st.markdown(
        """
        <div class="kintsugi-action-bar">
            <div class="kintsugi-action-pill">
                <div class="kintsugi-pill-icon">⟳</div>
                <div>
                    <div class="kintsugi-pill-text">Re-score Portfolio</div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #1A2E26;">Isolation Forest</div>
                </div>
            </div>
            <div class="kintsugi-action-pill">
                <div class="kintsugi-pill-icon">⚡</div>
                <div>
                    <div class="kintsugi-pill-text">Live Relief Simulator</div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #1A2E26;">Tenure & Grace Period</div>
                </div>
            </div>
            <div class="kintsugi-action-pill">
                <div class="kintsugi-pill-icon">📊</div>
                <div>
                    <div class="kintsugi-pill-text">Anomaly Triage</div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #1A2E26;">336 Severe Accounts</div>
                </div>
            </div>
            <div class="kintsugi-action-pill">
                <div class="kintsugi-pill-icon">🛡️</div>
                <div>
                    <div class="kintsugi-pill-text">RBI Compliance</div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #1A2E26;">FPC Validated</div>
                </div>
            </div>
            <div class="kintsugi-action-pill">
                <div class="kintsugi-pill-icon">⬇</div>
                <div>
                    <div class="kintsugi-pill-text">Audit Telemetry</div>
                    <div style="font-size: 0.76rem; font-weight: 700; color: #1A2E26;">Review 1 Package</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load data
    with st.spinner("Analyzing portfolio risk with Kintsugi Isolation Forest..."):
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
        st.markdown(
            """
            <h3 style="font-family: 'Cinzel', serif; color: #08201A;">
                📐 Kintsugi System Architecture & Regulatory Compliance Framework
            </h3>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            #### 1. Multi-Agent Autonomous Architecture
            - **Detection Agent**: Ingests non-linear spending metrics (spend-to-income, deal reliance ratio, liquidity runway, savings depletion velocity) and maps them into multidimensional space using an unsupervised **Isolation Forest** model (`n_estimators=150, contamination=0.15`).
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
