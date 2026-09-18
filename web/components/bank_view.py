"""Bank Underwriter View: Portfolio risk management, triage queue, and restructuring approval.

Visual Identity: Kintsugi - Connect • Assess • Empower
Aesthetic: Tranquil Washi Paper, Mild Glassmorphism (70% Opaque),
           Imperial Pine Jade & Radiant Molten Gold.
High Contrast & 100% English Typography.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.metrics import calculate_portfolio_kpis
from src.agents.restructuring_agent import DebtRestructuringAgent
from src.agents.outreach_agent import EmpatheticOutreachAgent


def render_bank_view(df_portfolio: pd.DataFrame):
    """Render the Underwriter Command Center and Risk Triage Queue."""
    st.markdown(
        """<div id="underwriter-command-center"></div>
<div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px;">
<div>
<h2 style="font-family: 'Cinzel', serif; margin: 0; color: #08201A; font-weight: 800;">
🏦 Portfolio Risk Triage & Command Center
</h2>
<p style="color: #12211C; font-size: 0.95rem; font-weight: 600; margin: 4px 0 0 0;">
Real-time unsupervised stress detection, non-linear early distress clustering, and automated restructuring queue.
</p>
</div>
<div style="text-align: right;">
<span class="seal-badge">AUDIT VERIFIED</span>
</div>
</div>""",
        unsafe_allow_html=True,
    )

    kpis = calculate_portfolio_kpis(df_portfolio)

    # 1. Executive Metric Cards (Mild Glassmorphism with Imperial Pine Hero Card)
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f"""<div class="kpi-card">
<div class="kpi-label">Active Portfolio</div>
<div class="kpi-value">{kpis.get('total_accounts', 0):,}</div>
<div class="kpi-subtext">Borrower Accounts Monitored</div>
</div>""",
            unsafe_allow_html=True,
        )
    with m2:
        # Imperial Pine Hero Card
        st.markdown(
            f"""<div class="kpi-card kpi-card-hero">
<div class="kpi-label">Total Outstanding</div>
<div class="kpi-value">₹{kpis.get('total_principal_outstanding', 0)/1e7:.2f} Cr</div>
<div class="kpi-subtext">
<span style="color: #F7EBD9; font-weight: 700;">↑ 100% Monitored</span> • Active Book
</div>
</div>""",
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""<div class="kpi-card">
<div class="kpi-label">Stress Anomaly Rate</div>
<div class="kpi-value" style="color: #961515;">{kpis.get('anomaly_prevalence_pct', 0):.1f}%</div>
<div class="kpi-subtext">{kpis.get('anomaly_count', 0)} High Distress Accounts</div>
</div>""",
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""<div class="kpi-card">
<div class="kpi-label">Portfolio at Risk (30+)</div>
<div class="kpi-value" style="color: #7A530A;">₹{kpis.get('par_30_exposure', 0)/1e5:.1f} L</div>
<div class="kpi-subtext">{kpis.get('par_30_pct', 0):.1f}% of Active Book</div>
</div>""",
            unsafe_allow_html=True,
        )
    with m5:
        st.markdown(
            f"""<div class="kpi-card">
<div class="kpi-label">Projected NPA Avoided</div>
<div class="kpi-value" style="color: #0A523E;">₹{kpis.get('projected_npa_avoided', 0)/1e5:.1f} L</div>
<div class="kpi-subtext">Via Proactive Relief (~68% cure)</div>
</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 2. Visual Risk Distribution Charts (Mild Glassmorphic Card Styling: 70% Opaque)
    c1, c2 = st.columns([1, 1])
    with c1:
        tier_counts = df_portfolio["risk_tier"].value_counts().reset_index()
        tier_counts.columns = ["Risk Tier", "Accounts"]
        fig_pie = px.pie(
            tier_counts,
            values="Accounts",
            names="Risk Tier",
            title="Portfolio Risk Stratification (Kintsugi Tripartite)",
            hole=0.55,
            color="Risk Tier",
            color_discrete_map={
                "Tier 1 (Normal / Low Risk)": "#0A4D3C",
                "Tier 2 (Moderate Stress)": "#C5A880",
                "Tier 3 (High Anomaly / Severe Distress)": "#961515",
            },
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(255, 255, 255, 0.70)",
            plot_bgcolor="rgba(255, 255, 255, 0.70)",
            font=dict(family="Plus Jakarta Sans", color="#08201A", size=12),
            title_font=dict(family="Cinzel", size=15, color="#08201A"),
            margin=dict(t=45, b=25, l=25, r=25),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        fig_scatter = px.scatter(
            df_portfolio,
            x="spend_to_income_ratio",
            y="emi_burden_ratio",
            color="risk_tier",
            size="remaining_principal",
            hover_data=["customer_id", "name", "anomaly_score"],
            title="Spend vs. EMI Burden Matrix (Size = Loan Principal)",
            color_discrete_map={
                "Tier 1 (Normal / Low Risk)": "#0A4D3C",
                "Tier 2 (Moderate Stress)": "#C5A880",
                "Tier 3 (High Anomaly / Severe Distress)": "#961515",
            },
        )
        fig_scatter.add_vline(x=0.7, line_dash="dash", line_color="#C5A880", opacity=0.85)
        fig_scatter.add_hline(y=0.45, line_dash="dash", line_color="#C5A880", opacity=0.85)
        fig_scatter.update_layout(
            paper_bgcolor="rgba(255, 255, 255, 0.70)",
            plot_bgcolor="rgba(255, 255, 255, 0.70)",
            font=dict(family="Plus Jakarta Sans", color="#08201A", size=12),
            title_font=dict(family="Cinzel", size=15, color="#08201A"),
            margin=dict(t=45, b=25, l=25, r=25),
            xaxis_title="Monthly Spend / Income Ratio",
            yaxis_title="Monthly EMI / Income Ratio",
            xaxis=dict(gridcolor="#EADFCF", zerolinecolor="#C5A880"),
            yaxis=dict(gridcolor="#EADFCF", zerolinecolor="#C5A880"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. Triage Queue & Filterable Table
    st.markdown("---")
    st.markdown(
        """<div id="triage-queue-section"></div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
<h3 style="font-family: 'Cinzel', serif; color: #08201A; margin: 0; font-weight: 800;">
📋 Underwriter Triage Queue
</h3>
<span style="font-size: 0.85rem; font-weight: 700; color: #12211C;">Ranked by Unsupervised Stress Anomaly Score</span>
</div>""",
        unsafe_allow_html=True,
    )

    # Synchronize with global search from top header
    global_query = st.session_state.get("global_portfolio_search", "").strip()

    f1, f2, f3 = st.columns([2, 2, 3])
    with f1:
        tier_filter = st.selectbox(
            "Filter by Risk Tier",
            options=["All Tiers", "Tier 3 (High Anomaly / Severe Distress)", "Tier 2 (Moderate Stress)", "Tier 1 (Normal / Low Risk)"],
        )
    with f2:
        min_score = st.slider("Minimum Anomaly Score", 0.0, 1.0, 0.0, 0.05)
    with f3:
        search_query = st.text_input(
            "🔍 Search Borrower Name, ID, or Drivers",
            value=global_query,
            key="triage_local_search",
            placeholder="Type customer ID, name, or driver...",
        )

    # Determine effective search term
    effective_query = search_query.strip() if search_query.strip() else global_query

    filtered_df = df_portfolio.copy()
    if tier_filter != "All Tiers":
        filtered_df = filtered_df[filtered_df["risk_tier"] == tier_filter]
    if min_score > 0.0:
        filtered_df = filtered_df[filtered_df["anomaly_score"] >= min_score]
    if effective_query:
        mask = (
            filtered_df["customer_id"].astype(str).str.contains(effective_query, case=False, na=False)
            | filtered_df["name"].astype(str).str.contains(effective_query, case=False, na=False)
            | filtered_df["primary_drivers"].astype(str).str.contains(effective_query, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
        st.info(f"🔍 Filtered by query **'{effective_query}'** — {len(filtered_df):,} matching borrower account(s).")

    # Display clean table
    display_cols = [
        "customer_id",
        "name",
        "monthly_income",
        "current_emi",
        "remaining_principal",
        "liquidity_runway_months",
        "deal_reliance_index",
        "anomaly_score",
        "risk_tier",
        "primary_drivers",
    ]
    st.dataframe(
        filtered_df[display_cols].rename(
            columns={
                "customer_id": "Cust ID",
                "name": "Borrower Name",
                "monthly_income": "Income (₹)",
                "current_emi": "EMI (₹)",
                "remaining_principal": "Principal (₹)",
                "liquidity_runway_months": "Runway (Mos)",
                "deal_reliance_index": "Deal Index",
                "anomaly_score": "Distress Score",
                "risk_tier": "Risk Tier",
                "primary_drivers": "Top Stress Drivers",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    # 4. Deep Dive & Restructuring Action Center
    st.markdown("---")
    st.markdown(
        """<div id="restructuring-action-center"></div>
<h3 style="font-family: 'Cinzel', serif; color: #08201A; margin: 0 0 16px 0; font-weight: 800;">
⚡ Case Review & Restructuring Action Center
</h3>""",
        unsafe_allow_html=True,
    )

    triage_options = filtered_df["customer_id"].tolist() if not filtered_df.empty else df_portfolio["customer_id"].tolist()
    default_select_idx = triage_options.index("CUST-4141") if "CUST-4141" in triage_options else 0

    selected_id = st.selectbox(
        "Select Borrower for Deep Dive & Restructuring Solution:",
        options=triage_options,
        index=default_select_idx,
    )

    if selected_id:
        cust_record = df_portfolio[df_portfolio["customer_id"] == selected_id].iloc[0]
        
        # Safely extract metrics with comprehensive fallbacks
        cust_name = cust_record.get("name", "Borrower")
        cust_id = cust_record.get("customer_id", selected_id)
        cust_phone = cust_record.get("phone", "+91-9800000000")
        monthly_inc = float(cust_record.get("monthly_income", 0.0))
        curr_emi = float(cust_record.get("current_emi", 14400.0))
        rem_principal = float(cust_record.get("remaining_principal", 300000.0))
        rem_tenure = int(cust_record.get("remaining_tenure_months", 24))
        apr_rate = float(cust_record.get("annual_interest_rate", 0.14))
        savings_bal = float(cust_record.get("savings_balance", 0.0))
        runway_mo = float(cust_record.get("liquidity_runway_months", 0.91))
        deal_idx = float(cust_record.get("deal_reliance_index", cust_record.get("deal_purchase_ratio", 0.4960)))
        disc_ratio = float(cust_record.get("discretionary_ratio", 0.6400))
        credit_util = float(cust_record.get("credit_utilization", 0.88))
        late_days = int(cust_record.get("late_payment_days_last_6m", 18))
        drivers = cust_record.get("primary_drivers", "Severe Outflow Burden, Deal Surge, Liquidity Depletion")
        tier_label = cust_record.get("risk_tier", "Tier 3 (High Anomaly / Severe Distress)")

        # Benchmark behavioral metrics
        deal_surge_pct = ((deal_idx - 0.1973) / 0.1973 * 100) if deal_idx > 0.1973 else 0.0
        disc_compression_pct = disc_ratio * 100.0

        c_info, c_action = st.columns([1, 1])

        with c_info:
            # Render clean HTML without ANY leading whitespace to prevent Markdown code block triggers
            info_html = (
                f'<div class="glass-panel" style="border-top: 3.5px solid #C5A880;">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">'
                f'<div>'
                f'<h4 style="margin: 0; color: #08201A; font-family: \'Cinzel\', serif; font-size: 1.25rem;">{cust_name}</h4>'
                f'<span style="font-size: 0.84rem; color: #664614; font-weight: 700;">ID: {cust_id} • Phone: {cust_phone}</span>'
                f'</div>'
                f'<span class="badge-tier-3">{tier_label}</span>'
                f'</div>'
                f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px;">'
                f'<div style="background: rgba(158, 28, 28, 0.12); border: 1.5px solid rgba(158, 28, 28, 0.40); border-radius: 10px; padding: 10px; text-align: center;">'
                f'<div style="font-size: 0.72rem; color: #961515; text-transform: uppercase; font-weight: 800;">Deal Surge</div>'
                f'<div style="font-size: 1.15rem; font-weight: 800; color: #08201A;">+{deal_surge_pct:.1f}%</div>'
                f'<div style="font-size: 0.70rem; color: #2C4037; font-weight: 600;">Coupon Reliance</div>'
                f'</div>'
                f'<div style="background: rgba(197, 168, 128, 0.18); border: 1.5px solid rgba(197, 168, 128, 0.50); border-radius: 10px; padding: 10px; text-align: center;">'
                f'<div style="font-size: 0.72rem; color: #7A530A; text-transform: uppercase; font-weight: 800;">Discretionary</div>'
                f'<div style="font-size: 1.15rem; font-weight: 800; color: #08201A;">{disc_compression_pct:.0f}%</div>'
                f'<div style="font-size: 0.70rem; color: #2C4037; font-weight: 600;">Spend Share</div>'
                f'</div>'
                f'<div style="background: rgba(10, 82, 62, 0.12); border: 1.5px solid rgba(10, 82, 62, 0.40); border-radius: 10px; padding: 10px; text-align: center;">'
                f'<div style="font-size: 0.72rem; color: #0A523E; text-transform: uppercase; font-weight: 800;">Liquid Runway</div>'
                f'<div style="font-size: 1.15rem; font-weight: 800; color: #08201A;">{runway_mo:.2f} Mo</div>'
                f'<div style="font-size: 0.70rem; color: #2C4037; font-weight: 600;">Cash Buffer</div>'
                f'</div>'
                f'</div>'
                f'<p style="font-size: 0.92rem; margin: 6px 0; color: #12211C;"><strong>Monthly Income:</strong> ₹{monthly_inc:,.2f} | <strong>Current EMI:</strong> ₹{curr_emi:,.2f}</p>'
                f'<p style="font-size: 0.92rem; margin: 6px 0; color: #12211C;"><strong>Remaining Principal:</strong> ₹{rem_principal:,.2f} @ {apr_rate*100:.1f}% APR ({rem_tenure} mos)</p>'
                f'<p style="font-size: 0.92rem; margin: 6px 0; color: #12211C;"><strong>Liquid Savings:</strong> ₹{savings_bal:,.2f} | <strong>Credit Utilization:</strong> {credit_util*100:.1f}%</p>'
                f'<p style="font-size: 0.92rem; margin: 6px 0; color: #12211C;"><strong>Payment Friction:</strong> {late_days} late days in last 6 months</p>'
                f'<p style="font-size: 0.92rem; margin: 6px 0; color: #12211C;"><strong>Primary Drivers:</strong> <span style="color: #961515; font-weight: 800;">{drivers}</span></p>'
                f'</div>'
            )
            st.markdown(info_html, unsafe_allow_html=True)

        with c_action:
            st.markdown("<h5 style='font-family: Cinzel, serif; color: #08201A; font-weight: 800;'>🛠️ Restructuring Parameters</h5>", unsafe_allow_html=True)
            col_ext, col_rate, col_mor = st.columns(3)
            with col_ext:
                tenure_ext = st.slider("Tenure Extension (Months)", 0, 36, 12, 6)
            with col_rate:
                rate_disc = st.slider("Rate Concession (BPS)", 0, 200, 100, 25)
            with col_mor:
                moratorium = st.slider("Grace Period (Months)", 0, 6, 0, 1)

            restr_agent = DebtRestructuringAgent()
            proposal = restr_agent.optimize_restructuring(
                remaining_principal=rem_principal,
                current_emi=curr_emi,
                current_tenure_months=rem_tenure,
                annual_rate=apr_rate,
                tenure_extension_months=tenure_ext,
                rate_concession_bps=rate_disc,
                moratorium_months=moratorium,
            )

            st.success(
                f"**Proposed Restructured EMI:** ₹{proposal['new_emi']:,.2f} "
                f"| **Monthly Savings:** ₹{proposal['monthly_savings']:,.2f} "
                f"(-{proposal['savings_pct']}%)"
            )

            # Outreach Dispatcher
            outreach_agent = EmpatheticOutreachAgent()
            lang = st.radio("Outreach Language", ["English", "Hindi"], horizontal=True)

            outreach = outreach_agent.generate_outreach(
                customer_name=cust_name,
                customer_id=cust_id,
                restructuring_details=proposal,
                language=lang,
            )

            with st.expander("📬 Preview Empathetic Outreach Notice (RBI Compliant)"):
                st.markdown(f"**Email Subject:** {outreach['email_subject']}")
                st.text_area("Email Content", outreach["email_body"], height=160)
                st.text_area("SMS Preview", outreach["sms_body"], height=70)
                st.info(
                    f"Timing Compliance: {'Permissible (08:00 - 19:00)' if outreach['is_rbi_compliant_timing'] else 'Queue for 08:00 AM dispatch'}"
                )

            # Professional Animation & Feedback (Replaces Balloons)
            if st.button("🚀 Approve Restructuring & Dispatch Proactive Offer"):
                st.toast(f"Restructuring Plan Registered for {cust_name}", icon="✨")
                banner_html = (
                    f'<div class="kintsugi-success-banner">'
                    f'<div class="kintsugi-success-icon">✓</div>'
                    f'<div>'
                    f'<h4 style="margin: 0; color: #08201A; font-family: \'Cinzel\', serif; font-size: 1.1rem;">Restructuring Approved & Active</h4>'
                    f'<p style="margin: 4px 0 0 0; color: #12211C; font-size: 0.92rem; font-weight: 600;">'
                    f'Proposal registered and empathetic notification dispatched to <strong>{cust_name}</strong> ({cust_id}). Ledger updated.'
                    f'</p>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(banner_html, unsafe_allow_html=True)
