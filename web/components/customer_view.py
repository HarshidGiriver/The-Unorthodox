"""Customer View: Mobile-friendly interactive loan restructuring and relief simulator."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.agents.restructuring_agent import DebtRestructuringAgent
from src.config import BANK_NAME, BANK_GRIEVANCE_OFFICER_NAME, BANK_GRIEVANCE_OFFICER_PHONE, BANK_GRIEVANCE_OFFICER_EMAIL


def render_customer_view(df_portfolio: pd.DataFrame):
    """Render the Borrower Relief Simulator and Self-Service Portal."""
    st.markdown("### 📱 Customer Relief Portal & Loan Restructuring Simulator")
    st.markdown(
        "A transparent, stress-free space designed to help you regain financial breathing room."
    )

    # Profile Selector for demo simulation
    col_sel, _ = st.columns([2, 2])
    with col_sel:
        # Default to a distressed customer if available
        distressed_ids = df_portfolio[df_portfolio["risk_tier"].str.contains("Tier 3|Tier 2", na=False)]["customer_id"].tolist()
        default_idx = 0 if distressed_ids else 0
        customer_options = df_portfolio["customer_id"].tolist()
        
        selected_cust_id = st.selectbox(
            "Select Borrower Account (Demo Persona):",
            options=customer_options,
            index=customer_options.index(distressed_ids[0]) if distressed_ids else 0,
        )

    customer = df_portfolio[df_portfolio["customer_id"] == selected_cust_id].iloc[0]

    # Container Card
    st.markdown(
        f"""
        <div class="glass-panel" style="max-width: 800px; margin: 0 auto 24px auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 16px;">
                <div>
                    <h3 style="margin: 0; color: #ffffff;">Welcome, {customer['name']}</h3>
                    <span style="font-size: 0.85rem; color: #94a3b8;">Account ID: {customer['customer_id']} • {BANK_NAME}</span>
                </div>
                <div class="rbi-badge">
                    ✓ RBI Fair Practices Verified
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; text-align: center;">
                <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">Current Monthly EMI</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #f8fafc;">₹{customer['current_emi']:,.2f}</div>
                </div>
                <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">Outstanding Balance</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #818cf8;">₹{customer['remaining_principal']:,.2f}</div>
                </div>
                <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">Remaining Tenure</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: #34d399;">{int(customer['remaining_tenure_months'])} Months</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Interactive Simulator Sliders
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("#### ⚙️ Adjust Your Relief Preferences")
        tenure_extension = st.slider(
            "Extend Loan Duration (Months):",
            min_value=0,
            max_value=36,
            value=18,
            step=6,
            help="Extending tenure spreads out repayment, immediately lowering your required monthly payment.",
        )

        moratorium = st.slider(
            "Grace Period / Moratorium (Months):",
            min_value=0,
            max_value=6,
            value=0,
            step=1,
            help="Principal freeze period allowing you to stabilize personal emergency cash flow.",
        )

        rate_discount_bps = 75  # Bank pre-approved standard concession

        # Calculate live proposal
        solver = DebtRestructuringAgent()
        relief_plan = solver.optimize_restructuring(
            remaining_principal=customer["remaining_principal"],
            current_emi=customer["current_emi"],
            current_tenure_months=int(customer["remaining_tenure_months"]),
            annual_rate=customer["annual_interest_rate"],
            tenure_extension_months=tenure_extension,
            rate_concession_bps=rate_discount_bps,
            moratorium_months=moratorium,
        )

    with c_right:
        st.markdown("#### 💡 Your Immediate Relief Summary")
        savings = relief_plan["monthly_savings"]
        pct = relief_plan["savings_pct"]

        st.markdown(
            f"""
            <div class="glass-panel" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(16, 185, 129, 0.3);">
                <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 4px;">RESTRUCTURED MONTHLY PAYMENT</div>
                <div style="font-size: 2.2rem; font-weight: 700; color: #34d399; margin-bottom: 8px;">
                    ₹{relief_plan['new_emi']:,.2f} <span style="font-size: 1rem; color: #94a3b8;">/ month</span>
                </div>
                <div class="relief-chip">
                    Save ₹{savings:,.2f} per month ({pct:.1f}% reduction)
                </div>
                <div style="margin-top: 16px; font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                    • New Loan Tenure: <strong>{relief_plan['new_tenure_months']} months</strong><br>
                    • Concessional APR: <strong>{relief_plan['new_annual_rate']*100:.2f}%</strong> (75 bps discount applied)<br>
                    • Grace Period: <strong>{relief_plan['moratorium_months']} months</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Visual Amortization Schedule
    st.markdown("---")
    st.subheader("📊 Projected Repayment & Balance Trajectory")

    sched = relief_plan["amortization_schedule"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sched["month"],
            y=sched["ending_balance"],
            mode="lines",
            name="Remaining Principal Balance",
            line=dict(color="#6366f1", width=3),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.1)",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sched["month"],
            y=sched["principal_paid"],
            name="Principal Component",
            marker_color="#10b981",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sched["month"],
            y=sched["interest_paid"],
            name="Interest Component",
            marker_color="#f59e0b",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        margin=dict(t=30, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Transparent Statutory Acceptance
    st.markdown("---")
    st.markdown("#### 📜 Statutory Terms & Single-Click Acceptance")
    st.info(
        f"**Statutory Disclosure under RBI Fair Practices Code for Lenders (FPC):**\n\n"
        f"1. This restructuring offer is entirely voluntary and is extended to assist you during temporary cash flow tightness.\n"
        f"2. Total lifetime interest on restructured plan is ₹{relief_plan['total_interest_new']:,.2f} (compared to ₹{relief_plan['total_interest_old']:,.2f} on original terms due to tenure extension).\n"
        f"3. For grievances or complaints, contact Bank Grievance Redressal Officer: "
        f"**{BANK_GRIEVANCE_OFFICER_NAME}** | Phone: **{BANK_GRIEVANCE_OFFICER_PHONE}** | Email: **{BANK_GRIEVANCE_OFFICER_EMAIL}**."
    )

    consent = st.checkbox("I have reviewed the restructured schedule and agree to the revised repayment terms.")

    if st.button("✅ Confirm & Activate Restructured Payment Plan", disabled=not consent):
        st.balloons()
        st.success(
            f"Congratulations {customer['name']}! Your restructured plan has been activated. "
            f"Your next EMI will be ₹{relief_plan['new_emi']:,.2f}. An updated agreement and schedule "
            f"have been sent to your registered email."
        )
