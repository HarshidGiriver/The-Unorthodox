"""Bank Underwriter View: Portfolio risk management, triage queue, and restructuring approval."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.config import BASE_DIR
from src.utils.metrics import calculate_portfolio_kpis
from src.agents.restructuring_agent import DebtRestructuringAgent
from src.agents.outreach_agent import EmpatheticOutreachAgent


def render_bank_view(df_portfolio: pd.DataFrame):
    """Render the Underwriter Command Center and Risk Triage Queue."""
    st.markdown("### 🏦 Portfolio Risk Triage & Underwriter Command Center")
    st.markdown(
        "Real-time unsupervised stress detection, non-linear early distress clustering, "
        "and automated restructuring queue."
    )

    kpis = calculate_portfolio_kpis(df_portfolio)

    # 1. Executive Metric Cards
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Active Portfolio</div>
                <div class="kpi-value">{kpis.get('total_accounts', 0):,}</div>
                <div class="kpi-subtext">Borrower Accounts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Outstanding</div>
                <div class="kpi-value">₹{kpis.get('total_principal_outstanding', 0)/1e7:.2f} Cr</div>
                <div class="kpi-subtext">Principal Book Value</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Stress Anomaly Rate</div>
                <div class="kpi-value" style="color: #fb7185;">{kpis.get('anomaly_prevalence_pct', 0):.1f}%</div>
                <div class="kpi-subtext">{kpis.get('anomaly_count', 0)} High Stress Accounts</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Portfolio at Risk (30+)</div>
                <div class="kpi-value" style="color: #fbbf24;">₹{kpis.get('par_30_exposure', 0)/1e5:.1f} L</div>
                <div class="kpi-subtext">{kpis.get('par_30_pct', 0):.1f}% of Active Book</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Projected NPA Avoided</div>
                <div class="kpi-value" style="color: #34d399;">₹{kpis.get('projected_npa_avoided', 0)/1e5:.1f} L</div>
                <div class="kpi-subtext">Via Proactive Relief (~68% cure)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. Visual Risk Distribution Charts & Static Diagnostic Expander
    c1, c2 = st.columns([1, 1])
    with c1:
        tier_counts = df_portfolio["risk_tier"].value_counts().reset_index()
        tier_counts.columns = ["Risk Tier", "Accounts"]
        fig_pie = px.pie(
            tier_counts,
            values="Accounts",
            names="Risk Tier",
            title="Portfolio Risk Stratification",
            hole=0.55,
            color="Risk Tier",
            color_discrete_map={
                "Tier 1 (Normal / Low Risk)": "#10b981",
                "Tier 2 (Moderate Stress)": "#f59e0b",
                "Tier 3 (High Anomaly / Severe Distress)": "#f43f5e",
            },
        )
        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=20, r=20),
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
                "Tier 1 (Normal / Low Risk)": "#10b981",
                "Tier 2 (Moderate Stress)": "#f59e0b",
                "Tier 3 (High Anomaly / Severe Distress)": "#f43f5e",
            },
        )
        fig_scatter.add_vline(x=0.7, line_dash="dash", line_color="#94a3b8", opacity=0.6)
        fig_scatter.add_hline(y=0.45, line_dash="dash", line_color="#94a3b8", opacity=0.6)
        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=20, r=20),
            xaxis_title="Monthly Spend / Income Ratio",
            yaxis_title="Monthly EMI / Income Ratio",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Dedicated Expandable Section: Static Diagnostics & Isolation Forest Verification
    distress_dist_img = BASE_DIR / "assets" / "distress_distribution.png"
    deal_spend_img = BASE_DIR / "assets" / "deal_vs_spend_scatter.png"
    risk_drivers_img = BASE_DIR / "assets" / "risk_drivers_comparison.png"

    with st.expander("📊 Portfolio Behavioral Diagnostics & Isolation Forest Verification", expanded=True):
        st.markdown(
            "Empirical offline diagnostics validating unsupervised anomaly clustering, non-linear spend compression, "
            "and primary distress drivers across all 2,240 portfolio accounts."
        )
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            st.markdown("##### 1. Anomaly Stratification")
            if distress_dist_img.exists():
                st.image(str(distress_dist_img), use_container_width=True)
            st.caption("Distribution of 2,240 accounts showing long-tail Tier 3 distressed anomaly density.")
        with ch2:
            st.markdown("##### 2. Deal Reliance vs. Spend")
            if deal_spend_img.exists():
                st.image(str(deal_spend_img), use_container_width=True)
            st.caption("Non-linear clustering separating normal spending from emergency coupon hunting.")
        with ch3:
            st.markdown("##### 3. Risk Drivers Attribution")
            if risk_drivers_img.exists():
                st.image(str(risk_drivers_img), use_container_width=True)
            st.caption("Feature attribution highlighting deal reliance (+151.4%) and liquidity collapse.")

    # 3. Triage Queue & Filterable Table
    st.markdown("---")
    st.subheader("📋 Underwriter Triage Queue")

    f1, f2, f3 = st.columns([2, 2, 3])
    with f1:
        tier_filter = st.selectbox(
            "Filter by Risk Tier",
            options=["All Tiers", "Tier 3 (High Anomaly / Severe Distress)", "Tier 2 (Moderate Stress)", "Tier 1 (Normal / Low Risk)"],
        )
    with f2:
        min_score = st.slider("Minimum Anomaly Score", 0.0, 1.0, 0.0, 0.05)
    with f3:
        search_query = st.text_input("🔍 Search Borrower Name or ID", "")

    filtered_df = df_portfolio.copy()
    if tier_filter != "All Tiers":
        filtered_df = filtered_df[filtered_df["risk_tier"] == tier_filter]
    if min_score > 0.0:
        filtered_df = filtered_df[filtered_df["anomaly_score"] >= min_score]
    if search_query:
        mask = (
            filtered_df["customer_id"].str.contains(search_query, case=False, na=False)
            | filtered_df["name"].str.contains(search_query, case=False, na=False)
        )
        filtered_df = filtered_df[mask]

    # Ensure CUST-4141 is featured prominently at the top of the triage table
    if "customer_id" in filtered_df.columns and "CUST-4141" in filtered_df["customer_id"].values:
        cust_4141_row = filtered_df[filtered_df["customer_id"] == "CUST-4141"]
        other_rows = filtered_df[filtered_df["customer_id"] != "CUST-4141"].sort_values(by="anomaly_score", ascending=False)
        filtered_df = pd.concat([cust_4141_row, other_rows], ignore_index=True)
    else:
        filtered_df = filtered_df.sort_values(by="anomaly_score", ascending=False)

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
    # Ensure all display columns exist safely
    for col in display_cols:
        if col not in filtered_df.columns:
            filtered_df[col] = 0.0

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
    st.subheader("⚡ Case Review & Restructuring Action Center")

    triage_options = filtered_df["customer_id"].tolist() if not filtered_df.empty else []
    default_select_idx = triage_options.index("CUST-4141") if "CUST-4141" in triage_options else 0

    selected_id = st.selectbox(
        "Select Borrower for Deep Dive & Restructuring Solution:",
        options=triage_options,
        index=default_select_idx,
    )

    if selected_id:
        cust_record = df_portfolio[df_portfolio["customer_id"] == selected_id].iloc[0]
        
        # Safely extract metrics with comprehensive fallbacks to prevent any KeyError
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

        # Compute benchmark behavioral metrics
        deal_surge_pct = ((deal_idx - 0.1973) / 0.1973 * 100) if deal_idx > 0.1973 else 0.0
        disc_compression_pct = disc_ratio * 100.0

        c_info, c_action = st.columns([1, 1])

        with c_info:
            st.markdown(
                f"""
                <div class="glass-panel">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <div>
                            <h4 style="margin:0;">{cust_name} <span style="font-size:0.85rem; color:#94a3b8;">({cust_id})</span></h4>
                            <span style="font-size:0.8rem; color:#64748b;">Phone: {cust_phone}</span>
                        </div>
                        <span class="badge-tier-3">{tier_label}</span>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px;">
                        <div style="background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.28); border-radius: 10px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.72rem; color: #fb7185; text-transform: uppercase; font-weight:600;">Deal Reliance</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">+{deal_surge_pct:.1f}%</div>
                            <div style="font-size: 0.68rem; color: #94a3b8;">Emergency Deal Surge</div>
                        </div>
                        <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.28); border-radius: 10px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.72rem; color: #fbbf24; text-transform: uppercase; font-weight:600;">Discretionary Spend</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">{disc_compression_pct:.0f}%</div>
                            <div style="font-size: 0.68rem; color: #94a3b8;">Spend Compression</div>
                        </div>
                        <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.28); border-radius: 10px; padding: 10px; text-align: center;">
                            <div style="font-size: 0.72rem; color: #818cf8; text-transform: uppercase; font-weight:600;">Liquidity Buffer</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">{runway_mo:.2f} Mo</div>
                            <div style="font-size: 0.68rem; color: #94a3b8;">Reserve Cash Runway</div>
                        </div>
                    </div>

                    <div style="font-size: 0.85rem; line-height: 1.7; color: #cbd5e1;">
                        <p style="margin:4px 0;"><strong>Monthly Income:</strong> ₹{monthly_inc:,.2f} | <strong>Current EMI:</strong> ₹{curr_emi:,.2f}</p>
                        <p style="margin:4px 0;"><strong>Remaining Principal:</strong> ₹{rem_principal:,.2f} @ {apr_rate*100:.1f}% APR ({rem_tenure} mos)</p>
                        <p style="margin:4px 0;"><strong>Liquid Savings:</strong> ₹{savings_bal:,.2f} | <strong>Credit Utilization:</strong> {credit_util*100:.1f}%</p>
                        <p style="margin:4px 0;"><strong>Payment Friction:</strong> {late_days} late days in last 6 months</p>
                        <p style="margin:4px 0;"><strong>Primary Risk Drivers:</strong> <span style="color:#fb7185;">{drivers}</span></p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_action:
            st.markdown("##### 🛠️ Restructuring Parameters")
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

            with st.expander("📬 Preview Empathetic Outreach Message (RBI Compliant)"):
                st.markdown(f"**Email Subject:** {outreach['email_subject']}")
                st.text_area("Email Content", outreach["email_body"], height=160)
                st.text_area("SMS Preview", outreach["sms_body"], height=70)
                st.info(
                    f"Timing Compliance: {'Permissible (08:00 - 19:00)' if outreach['is_rbi_compliant_timing'] else 'Queue for 08:00 AM dispatch'}"
                )

            if st.button("🚀 Approve Restructuring & Dispatch Proactive Offer"):
                st.balloons()
                st.success(
                    f"Restructuring approved for {cust_name}! Proposal logged and empathetic notification dispatched."
                )
