"""Bank Underwriter View: Portfolio risk management, triage queue, and restructuring approval."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

    # 2. Visual Risk Distribution Charts
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
    st.subheader("⚡ Case Review & Restructuring Action Center")

    selected_id = st.selectbox(
        "Select Borrower for Deep Dive & Restructuring Solution:",
        options=filtered_df["customer_id"].tolist() if not filtered_df.empty else [],
    )

    if selected_id:
        cust_record = df_portfolio[df_portfolio["customer_id"] == selected_id].iloc[0]
        
        c_info, c_action = st.columns([1, 1])

        with c_info:
            st.markdown(
                f"""
                <div class="glass-panel">
                    <h4>{cust_record['name']} <span style="font-size:0.9rem; color:#94a3b8;">({cust_record['customer_id']})</span></h4>
                    <p><strong>Contact:</strong> {cust_record.get('phone', 'N/A')}</p>
                    <p><strong>Monthly Income:</strong> ₹{cust_record['monthly_income']:,.2f} | <strong>Current EMI:</strong> ₹{cust_record['current_emi']:,.2f}</p>
                    <p><strong>Remaining Principal:</strong> ₹{cust_record['remaining_principal']:,.2f} @ {cust_record['annual_interest_rate']*100:.1f}% APR</p>
                    <p><strong>Liquid Buffer:</strong> ₹{cust_record['savings_balance']:,.2f} ({cust_record['liquidity_runway_months']} months)</p>
                    <p><strong>Primary Drivers:</strong> <span style="color:#fb7185;">{cust_record['primary_drivers']}</span></p>
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
                remaining_principal=cust_record["remaining_principal"],
                current_emi=cust_record["current_emi"],
                current_tenure_months=int(cust_record["remaining_tenure_months"]),
                annual_rate=cust_record["annual_interest_rate"],
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
                customer_name=cust_record["name"],
                customer_id=cust_record["customer_id"],
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
                    f"Restructuring approved for {cust_record['name']}! Proposal logged and empathetic notification dispatched."
                )
