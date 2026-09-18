"""Kintsugi AI: Autonomous Financial Distress Detection & Debt Restructuring Engine.

Visual Identity: Kintsugi - Connect • Assess • Empower
Aesthetic: Tranquil Washi Paper, Mild Glassmorphism (70% Opaque),
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
    # Initialize navigation state
    NAV_TABS = [
        "🏦 Underwriter Command Center",
        "📱 Customer Relief Simulator",
        "📑 Architecture & RBI Framework",
    ]
    if "nav_tab_selection" not in st.session_state:
        st.session_state["nav_tab_selection"] = NAV_TABS[0]

    # 1. Sidebar Brand & Controls
    with st.sidebar:
        # Display Kintsugi Logo
        logo_path = BASE_DIR / "assets" / "kintsugi_logo_thumb.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "assets" / "kintsugi_logo.jpg"

        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)

        st.markdown(
            """<div style="text-align: center; margin-top: -8px; margin-bottom: 16px;">
<div style="font-size: 0.78rem; font-weight: 800; letter-spacing: 0.16em; color: #664614; text-transform: uppercase;">
Connect • Assess • Empower
</div>
</div>""",
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ System Controls")
        st.info("Unsupervised Isolation Forest + Deterministic Amortization Solver")

        if st.button("🔄 Refresh / Re-score Portfolio", use_container_width=True, key="sidebar_rescore"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # Kintsugi Philosophy Callout (English Only)
        st.markdown(
            """<div class="kintsugi-callout" style="padding: 14px 16px; margin-bottom: 16px;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
<span class="seal-badge">KINTSUGI</span>
<strong style="font-family: 'Cinzel', serif; font-size: 0.88rem; color: #08201A;">The Philosophy</strong>
</div>
<div style="font-size: 0.82rem; color: #12211C; font-weight: 600; line-height: 1.5;">
The ancient art of repairing ceramics with gold lacquer. Financial hardship is treated not as a failure to hide, but as an opportunity to restore credit health with dignity.
</div>
</div>""",
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
            """<div style="display: flex; align-items: center; gap: 12px; padding: 6px 0;">
<div class="kintsugi-avatar">RO</div>
<div>
<div style="font-size: 0.88rem; font-weight: 800; color: #08201A;">Risk Operations Command</div>
<div style="font-size: 0.78rem; font-weight: 700; color: #664614;">Enterprise Lead Underwriter</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )

    # 2. Live Interactive Top Navigation & Search Bar
    st.markdown('<div class="kintsugi-top-nav-wrapper">', unsafe_allow_html=True)
    c_nav_search, c_nav_user = st.columns([1.1, 1.9], gap="medium")
    with c_nav_search:
        st.text_input(
            "Live Search",
            placeholder="🔍 Search borrower ID, name, or distress drivers...",
            key="global_portfolio_search",
            label_visibility="collapsed",
        )
    with c_nav_user:
        st.markdown(
            f"""<div class="kintsugi-user-pill">
<div class="rbi-badge">✓ RBI Fair Practices Verified</div>
<div style="font-size: 0.84rem; font-weight: 800; color: #0A2B24; border-left: 1.5px solid #C5A880; padding-left: 12px;">Enterprise: {BANK_NAME}</div>
<div style="display: flex; align-items: center; gap: 8px;">
<div class="kintsugi-avatar">RO</div>
<div style="font-size: 0.84rem; font-weight: 800; color: #08201A;">Underwriter Session Active</div>
</div>
</div>""",
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. Kintsugi Hero Banner (Mild Glassmorphism, High Contrast, English Only)
    hero_html = (
        f'<div class="kintsugi-hero-banner">'
        f'<div class="kintsugi-hero-content">'
        f'<div class="kintsugi-greeting-tag">'
        f'<span class="brand-badge" style="font-size: 0.72rem; padding: 3px 10px;">Enterprise Risk Engine v1.0</span>'
        f'<span style="font-weight: 800; color: #664614;">Autonomous Resolution</span>'
        f'</div>'
        f'<h1 class="kintsugi-hero-title">Build your financial tomorrow.</h1>'
        f'<p class="kintsugi-hero-subtitle">'
        f'Better insights. Smarter decisions. A stronger you.<br>'
        f'Proactive non-linear anomaly detection • Deterministic loan amortization • Dignified relief'
        f'</p>'
        f'<a href="#triage-queue-section" target="_self" class="kintsugi-btn-primary" onclick="document.getElementById(\'triage-queue-section\')?.scrollIntoView({{behavior: \'smooth\'}})">'
        f'View Portfolio Triage →'
        f'</a>'
        f'</div>'
        f'<div class="kintsugi-slogan-vertical">'
        f'REBUILD STRONGER • EMPOWER FUTURE'
        f'</div>'
        f'</div>'
    )
    st.markdown(hero_html, unsafe_allow_html=True)

    # 4. Interactive Quick Action Buttons Bar
    p1, p2, p3, p4, p5 = st.columns(5)
    with p1:
        if st.button("⟳ Re-score Portfolio", use_container_width=True, key="pill_btn_rescore"):
            st.cache_data.clear()
            st.rerun()
    with p2:
        if st.button("⚡ Live Relief Simulator", use_container_width=True, key="pill_btn_simulator"):
            st.session_state["nav_tab_selection"] = NAV_TABS[1]
            st.rerun()
    with p3:
        if st.button("📊 View Portfolio Triage", use_container_width=True, key="pill_btn_triage"):
            st.session_state["nav_tab_selection"] = NAV_TABS[0]
            st.rerun()
    with p4:
        if st.button("🛡️ RBI Compliance", use_container_width=True, key="pill_btn_rbi"):
            st.session_state["nav_tab_selection"] = NAV_TABS[2]
            st.rerun()
    with p5:
        if st.button("📑 Architecture Docs", use_container_width=True, key="pill_btn_docs"):
            st.session_state["nav_tab_selection"] = NAV_TABS[2]
            st.rerun()

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Load data
    with st.spinner("Analyzing portfolio risk with Kintsugi Isolation Forest..."):
        df_portfolio = load_and_score_portfolio()

    # 5. Interactive Navigation Tabs
    active_tab = st.radio(
        "Navigation Selector",
        options=NAV_TABS,
        index=NAV_TABS.index(st.session_state["nav_tab_selection"]),
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav_radio",
    )
    st.session_state["nav_tab_selection"] = active_tab

    if active_tab == NAV_TABS[0]:
        render_bank_view(df_portfolio)
    elif active_tab == NAV_TABS[1]:
        render_customer_view(df_portfolio)
    elif active_tab == NAV_TABS[2]:
        st.markdown(
            """<h3 style="font-family: 'Cinzel', serif; color: #08201A;">
📐 Kintsugi System Architecture & Regulatory Compliance Framework
</h3>""",
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
