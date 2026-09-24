"""Authenticated UI for the persisted local workflow."""

import sqlite3
import pandas as pd
import streamlit as st

from backend.auth import login, logout
from integration.services import application_workflow


def show_terms(proposal):
    plan = proposal["terms"]
    st.subheader(f"Proposal v{proposal['version']} · {proposal['customer_id']} · {proposal['status']}")
    st.caption(f"Reference: {proposal['id']}")
    from backend.config import BANK_GRIEVANCE_OFFICER_NAME, BANK_GRIEVANCE_OFFICER_EMAIL, BANK_GRIEVANCE_OFFICER_PHONE
    st.info(f"Voluntary proposal. Questions: {BANK_GRIEVANCE_OFFICER_NAME}, "
            f"{BANK_GRIEVANCE_OFFICER_EMAIL}, {BANK_GRIEVANCE_OFFICER_PHONE}. Contact details are configured by the operator.")
    st.table(pd.DataFrame({
        "Term": ["Regular monthly payment (INR)", "Remaining months", "APR (%)", "Total interest (INR)"],
        "Current": [plan["old_emi"], plan["old_tenure_months"], plan["old_annual_rate"] * 100, plan["total_interest_old"]],
        "Proposed": [plan["new_emi"], plan["new_tenure_months"], plan["new_annual_rate"] * 100, plan["total_interest_new"]],
    }))
    st.write(f"Interest-only period: {plan['moratorium_months']} months at INR {plan['moratorium_payment']:,.2f}/month. "
             "Regular payments follow; the last installment may differ by rounding.")
    st.write(f"Available monthly income after expenses: INR {plan['available_income']:,.2f}.")
    if not plan["affordable"]:
        st.error("Payments exceed available income. This proposal cannot be approved.")
    if not plan["target_met"]:
        st.warning(plan["target_status"])
    if plan["simulation"]:
        st.warning("Simulated finances. Activation updates this local demonstration database only.")
    schedule = pd.DataFrame(plan["amortization_schedule"])
    with st.expander("Full repayment schedule"):
        st.dataframe(schedule, hide_index=True)
    st.download_button("Download these exact terms and schedule", schedule.to_csv(index=False),
                       file_name=f"proposal-{proposal['id']}-v{proposal['version']}.csv", mime="text/csv",
                       key=f"download_{proposal['id']}")


def render_workflow():
    st.title("Kintsugi AI · Saved workflow")
    st.caption("Local loan proposals, approvals, consent and receipt tracking. No core banking connection.")
    workflow = application_workflow()
    token = st.session_state.get("auth_token")
    if token:
        try:
            actor = workflow.principal(token)
        except PermissionError:
            st.session_state.pop("auth_token", None)
            token = None
    if not token:
        st.info("Set up accounts with the local operator commands in README.md. No default passwords are supplied.")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            try:
                st.session_state["auth_token"] = login(workflow.database, username, password)
                st.rerun()
            except PermissionError as exc:
                st.error(str(exc))
        return
    st.sidebar.write(f"Signed in as {actor['username']} ({actor['role']})")
    if st.sidebar.button("Sign out"):
        logout(workflow.database, token)
        st.session_state.clear()
        st.rerun()
    try:
        portfolio = workflow.portfolio(token)
        if portfolio.empty:
            st.info("No accounts imported. Use the local operator import command.")
            return
        for key in ("data_warning", "scoring_warning"):
            if portfolio.attrs.get(key):
                st.warning(portfolio.attrs[key])
        st.caption("Anomaly scores are indicators for review, not probabilities of default.")
        if actor["role"] == "underwriter":
            st.dataframe(portfolio[["customer_id", "name", "anomaly_score", "risk_tier"]], hide_index=True)
            with st.form("create_proposal"):
                customer = st.selectbox("Borrower to review", portfolio["customer_id"].tolist())
                extension = st.slider("Extension in months", 0, 36, 12)
                concession = st.slider("Rate reduction in basis points", 0, 200, 100, 25)
                moratorium = st.slider("Interest-only months", 0, 6, 0)
                submitted = st.form_submit_button("Save draft for review")
            if submitted:
                proposal_id = workflow.create_proposal(token, customer, tenure_extension_months=extension,
                                                       rate_concession_bps=concession, moratorium_months=moratorium)
                st.success(f"Draft saved: {proposal_id}. Approval is a separate review action.")
        proposals = workflow.proposals(token)
        if not proposals:
            st.info("No proposals available for review.")
        else:
            selected = st.selectbox("Saved proposal", [p["id"] for p in proposals],
                                    format_func=lambda value: next(
                                        f"{p['customer_id']} · v{p['version']} · {p['status']}" for p in proposals if p["id"] == value
                                    ))
            proposal = next(p for p in proposals if p["id"] == selected)
            show_terms(proposal)
            if actor["role"] == "underwriter" and proposal["status"] == "draft":
                with st.form(f"review_{selected}"):
                    decision = st.selectbox("Review decision", ["Approve", "Reject"])
                    reason = st.text_area("Review rationale (required)")
                    reviewed = st.checkbox("I reviewed affordability, the full schedule and the anomaly context.")
                    submit = st.form_submit_button("Record decision")
                if submit:
                    if not reviewed:
                        raise ValueError("Confirm the review before recording a decision")
                    workflow.decide(token, selected, decision == "Approve", reason)
                    st.rerun()
            if actor["role"] == "borrower" and proposal["status"] == "approved":
                consent = st.checkbox("I reviewed these exact terms and voluntarily accept this proposal.",
                                      key=f"consent_{selected}_{proposal['terms_hash']}")
                if st.button("Record my consent", disabled=not consent):
                    workflow.consent(token, selected, proposal["terms_hash"])
                    st.rerun()
            if proposal["status"] == "consented" and st.button("Activate accepted plan in local ledger"):
                workflow.activate(token, selected)
                st.rerun()
            if proposal["status"] == "active":
                st.success("Accepted schedule is stored in the local ledger. External delivery is tracked separately.")
            summary = workflow.repayment_summary(token, proposal["customer_id"])
            st.write(summary)
        if actor["role"] == "underwriter":
            with st.expander("Record a payment receipt"):
                with st.form("payment"):
                    customer = st.selectbox("Receipt account", portfolio["customer_id"].tolist())
                    amount = st.number_input("Amount received (INR)", min_value=0.01, value=100.0)
                    reference = st.text_input("Unique receipt reference")
                    submit = st.form_submit_button("Record receipt")
                if submit:
                    workflow.record_payment(token, customer, amount, reference)
                    st.success("Receipt recorded; this does not reconcile principal automatically.")
            activity = workflow.activity(token)
            with st.expander("Delivery queue and audit history"):
                st.dataframe(pd.DataFrame(activity["delivery"]), hide_index=True)
                st.dataframe(pd.DataFrame(activity["events"]), hide_index=True)
    except (ValueError, PermissionError, sqlite3.IntegrityError) as exc:
        st.error(str(exc))
