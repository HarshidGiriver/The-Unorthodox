"""Customer View: Mobile-friendly interactive loan restructuring and relief simulator.

Visual Identity: Kintsugi - Connect • Assess • Empower
Aesthetic: Tranquil Washi Paper, Mild Glassmorphism (70% Opaque),
           Imperial Pine Jade & Radiant Molten Gold.
High Contrast & 100% English Typography.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from integration.services import DebtRestructuringAgent
from backend.config import BANK_NAME, BANK_GRIEVANCE_OFFICER_NAME, BANK_GRIEVANCE_OFFICER_PHONE, BANK_GRIEVANCE_OFFICER_EMAIL


def render_customer_view(df_portfolio: pd.DataFrame):
    """Render the Borrower Relief Simulator and Self-Service Portal."""
    st.markdown(
        """<div id="customer-portal-header"></div>
<div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px;">
<div>
<h2 style="font-family: 'Cinzel', serif; margin: 0; color: #08201A; font-weight: 800;">
 Borrower Relief Simulator & Self-Service Portal
</h2>
<p style="color: #12211C; font-size: 0.95rem; font-weight: 600; margin: 4px 0 0 0;">
A transparent, stress-free space designed to help you regain financial breathing room and rebuild credit health.
</p>
</div>
<div style="text-align: right;">
<span class="seal-badge">SIMULATED TERMS</span>
</div>
</div>""",
        unsafe_allow_html=True,
    )

    # Profile Selector for demo simulation
    col_sel, _ = st.columns([2, 2])
    with col_sel:
        customer_options = df_portfolio["customer_id"].tolist()
        previous = st.session_state.get("selected_customer_id", "CUST-4141")
        default_idx = customer_options.index(previous) if previous in customer_options else 0
        
        selected_cust_id = st.selectbox(
            "Select Borrower Account (Demo Persona):",
            options=customer_options,
            index=default_idx,
        )

    customer = df_portfolio[df_portfolio["customer_id"] == selected_cust_id].iloc[0]

    # Safely retrieve customer financial baseline
    cust_name = customer.get("name", "Borrower")
    cust_id = customer.get("customer_id", selected_cust_id)
    current_emi = float(customer.get("current_emi", 14403.86))
    rem_principal = float(customer.get("remaining_principal", 300000.0))
    baseline_tenure = int(customer.get("remaining_tenure_months", 24))
    annual_rate = float(customer.get("annual_interest_rate", 0.14))

    # Container Card (Mild Glassmorphism: 70% Opaque) - ZERO leading whitespace to prevent code blocks
    cust_card_html = (
        f'<div class="glass-panel" style="max-width: 820px; margin: 0 auto 24px auto; border-top: 3.5px solid #C5A880;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E5DDD2; padding-bottom: 14px; margin-bottom: 16px;">'
        f'<div>'
        f'<h3 style="margin: 0; color: #08201A; font-family: \'Cinzel\', serif; font-size: 1.3rem;">Welcome, {cust_name}</h3>'
        f'<span style="font-size: 0.88rem; font-weight: 700; color: #1A2E26;">Account ID: {cust_id} • {BANK_NAME}</span>'
        f'</div>'
        f'<div class="rbi-badge">'
        f'Demonstration'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; text-align: center;">'
        f'<div style="background: rgba(255, 255, 255, 0.70); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); padding: 14px; border-radius: 10px; border: 1px solid #E5DDD2;">'
        f'<div style="font-size: 0.80rem; color: #2D4239; text-transform: uppercase; font-weight: 800;">Current Monthly EMI</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #08201A; font-family: \'Cinzel\', serif;">₹{current_emi:,.2f}</div>'
        f'</div>'
        f'<div style="background: rgba(255, 255, 255, 0.70); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); padding: 14px; border-radius: 10px; border: 1px solid #E5DDD2;">'
        f'<div style="font-size: 0.80rem; color: #2D4239; text-transform: uppercase; font-weight: 800;">Outstanding Balance</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #664614; font-family: \'Cinzel\', serif;">₹{rem_principal:,.2f}</div>'
        f'</div>'
        f'<div style="background: rgba(255, 255, 255, 0.70); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); padding: 14px; border-radius: 10px; border: 1px solid #E5DDD2;">'
        f'<div style="font-size: 0.80rem; color: #2D4239; text-transform: uppercase; font-weight: 800;">Remaining Tenure</div>'
        f'<div style="font-size: 1.5rem; font-weight: 800; color: #0A523E; font-family: \'Cinzel\', serif;">{baseline_tenure} Months</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(cust_card_html, unsafe_allow_html=True)

    # Interactive Simulator Sliders
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("<h4 style='font-family: Cinzel, serif; color: #08201A; font-weight: 800;'>Adjust Your Relief Preferences</h4>", unsafe_allow_html=True)
        
        total_tenure = st.slider(
            "Revised Loan Duration (Months):",
            min_value=baseline_tenure,
            max_value=baseline_tenure + 36,
            value=36 if baseline_tenure <= 36 else baseline_tenure + 12,
            step=1,
            help="Adjust loan duration. Extending tenure spreads out repayment, immediately lowering your required monthly payment.",
        )
        tenure_extension = total_tenure - baseline_tenure

        st.caption(
            f"Original: **{baseline_tenure} mos** | Extension: **+{tenure_extension} mos** | Revised Tenure: **{total_tenure} mos**"
        )

        rate_discount_bps = st.slider(
            "Simulated Rate Concession (BPS):",
            min_value=0,
            max_value=200,
            value=100,
            step=25,
            help="Illustrative interest rate concession (100 bps = 1.00% reduction).",
        )

        moratorium = st.slider(
            "Grace Period / Moratorium (Months):",
            min_value=0,
            max_value=6,
            value=0,
            step=1,
            help="Principal freeze period allowing you to stabilize personal emergency cash flow.",
        )

        # Calculate live proposal
        solver = DebtRestructuringAgent()
        relief_plan = solver.optimize_restructuring(
            remaining_principal=rem_principal,
            current_emi=current_emi,
            current_tenure_months=baseline_tenure,
            annual_rate=annual_rate,
            tenure_extension_months=tenure_extension,
            rate_concession_bps=rate_discount_bps,
            moratorium_months=moratorium,
        )

    with c_right:
        st.markdown("<h4 style='font-family: Cinzel, serif; color: #08201A; font-weight: 800;'>Your Immediate Relief Summary</h4>", unsafe_allow_html=True)
        savings = relief_plan["monthly_savings"]
        pct = relief_plan["savings_pct"]

        # Imperial Pine Hero Relief Card
        hero_card_html = (
            f'<div class="kpi-card kpi-card-hero" style="border-radius: 16px; padding: 24px;">'
            f'<div style="font-size: 0.82rem; color: #F7EBD9; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 800;">'
            f'RESTRUCTURED MONTHLY PAYMENT'
            f'</div>'
            f'<div style="font-size: 2.35rem; font-weight: 800; color: #FFFFFF; margin: 4px 0 10px 0; font-family: \'Cinzel\', serif;">'
            f'₹{relief_plan["new_emi"]:,.2f} <span style="font-size: 1.05rem; color: #C5A880; font-family: sans-serif; font-weight: 600;">/ month</span>'
            f'</div>'
            f'<div class="relief-chip">'
            f'Save ₹{savings:,.2f} per month ({pct:.1f}% reduction)'
            f'</div>'
            f'<div style="margin-top: 18px; font-size: 0.90rem; color: #FFFFFF; font-weight: 500; line-height: 1.65;">'
            f'• New Repayment Horizon: <strong>{relief_plan["new_tenure_months"]} months</strong> (+{tenure_extension} mo extension)<br>'
            f'• Concessional APR: <strong>{relief_plan["new_annual_rate"]*100:.2f}%</strong> ({rate_discount_bps} bps discount applied)<br>'
            f'• Emergency Grace Period: <strong>{relief_plan["moratorium_months"]} months</strong> (Principal Freeze)'
            f'</div>'
            f'</div>'
        )
        st.markdown(hero_card_html, unsafe_allow_html=True)

    if not relief_plan["target_met"]:
        st.warning(relief_plan["target_status"])
    if moratorium:
        st.info(f"Interest-only payment during the first {moratorium} months: INR {relief_plan['moratorium_payment']:,.2f}. "
                f"Afterwards: INR {relief_plan['new_emi']:,.2f} per month; final installment may vary by rounding.")
    st.download_button("Download proposed repayment schedule", relief_plan["amortization_schedule"].to_csv(index=False),
                       file_name=f"{cust_id}-proposal.csv", mime="text/csv")
    # Visual Amortization Schedule (70% Mild Glassmorphism)
    st.markdown("---")
    st.markdown(
        """<h3 style="font-family: 'Cinzel', serif; color: #08201A; margin: 0 0 14px 0; font-weight: 800;">
 Projected Repayment & Balance Trajectory
</h3>""",
        unsafe_allow_html=True,
    )

    sched = relief_plan["amortization_schedule"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=sched["month"],
            y=sched["ending_balance"],
            mode="lines",
            name="Remaining Principal Balance",
            line=dict(color="#0A2B24", width=3.2),
            fill="tozeroy",
            fillcolor="rgba(197, 168, 128, 0.18)",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sched["month"],
            y=sched["principal_paid"],
            name="Principal Component",
            marker_color="#0A523E",
        )
    )
    fig.add_trace(
        go.Bar(
            x=sched["month"],
            y=sched["interest_paid"],
            name="Interest Component",
            marker_color="#C5A880",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(255, 255, 255, 0.70)",
        plot_bgcolor="rgba(255, 255, 255, 0.70)",
        font=dict(family="Plus Jakarta Sans", color="#08201A", size=12),
        title_font=dict(family="Cinzel", size=15, color="#08201A"),
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        xaxis=dict(gridcolor="#EADFCF", zerolinecolor="#C5A880", automargin=True, title_standoff=18),
        yaxis=dict(gridcolor="#EADFCF", zerolinecolor="#C5A880"),
        height=520,
        margin=dict(t=30, b=150, l=65, r=25),
        legend=dict(orientation="v", x=0, xanchor="left", yanchor="top", y=-0.3),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Transparent Statutory Acceptance
    st.markdown("---")
    st.markdown("<h4 style='font-family: Cinzel, serif; color: #08201A; font-weight: 800;'>Proposed Terms & Simulated Acceptance</h4>", unsafe_allow_html=True)
    st.info(
        f"**Illustrative repayment disclosures (not a certified legal notice):**\n\n"
        f"1. This restructuring offer is entirely voluntary and is extended to assist you during temporary cash flow tightness.\n"
        f"2. Total lifetime interest on restructured plan is ₹{relief_plan['total_interest_new']:,.2f} (compared to ₹{relief_plan['total_interest_old']:,.2f} on original terms due to tenure extension).\n"
        f"3. For grievances or complaints, contact Bank Grievance Redressal Officer: "
        f"**{BANK_GRIEVANCE_OFFICER_NAME}** | Phone: **{BANK_GRIEVANCE_OFFICER_PHONE}** | Email: **{BANK_GRIEVANCE_OFFICER_EMAIL}**."
    )

    consent = st.checkbox("I have reviewed the restructured schedule and agree to the revised repayment terms.")

    if st.button("Preview simulated acceptance", disabled=not consent):
        st.info("Simulation only: no repayment terms have changed and no agreement has been sent.")
