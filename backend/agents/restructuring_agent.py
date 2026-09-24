"""Debt Restructuring Agent: Deterministic debt amortization solver and relief optimizer."""

from typing import Dict, Any, Optional
from backend.finance import calculate_emi, number, integer
import pandas as pd

from backend.config import (
    MAX_TENURE_EXTENSION_MONTHS,
    MAX_RATE_CONCESSION_BPS,
    MAX_MORATORIUM_MONTHS,
)


class DebtRestructuringAgent:
    """Agent responsible for calculating deterministic, mathematically invariant debt restructuring plans."""

    @staticmethod
    def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
        """Calculate standard Equated Monthly Installment (EMI).

        Formula:
            EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)

        Args:
            principal: Remaining loan principal.
            annual_rate: Annual percentage interest rate (e.g. 0.12 for 12%).
            tenure_months: Number of monthly installment periods.

        Returns:
            Calculated monthly EMI rounded to 2 decimal places.
        """
        return calculate_emi(principal, annual_rate, tenure_months)

    def generate_amortization_schedule(
        self,
        principal: float,
        annual_rate: float,
        tenure_months: int,
        moratorium_months: int = 0,
    ) -> pd.DataFrame:
        """Generate month-by-month deterministic loan amortization schedule.

        Guarantees mathematical invariance:
        - Sum of principal components equals initial principal
        - Final balance equals 0.00 within round-off tolerance

        Args:
            principal: Initial principal balance.
            annual_rate: Annual interest rate (decimal).
            tenure_months: Total tenure in months (including moratorium).
            moratorium_months: Initial months of principal repayment freeze.

        Returns:
            DataFrame with monthly breakdown.
        """
        calculate_emi(principal, annual_rate, tenure_months)
        integer(moratorium_months, "moratorium_months", 0, min(MAX_MORATORIUM_MONTHS, tenure_months - 1))
        principal = round(principal, 2)
        r = annual_rate / 12.0
        active_tenure = tenure_months - moratorium_months
        normal_emi = self.calculate_emi(principal, annual_rate, active_tenure)

        schedule = []
        current_balance = float(principal)

        for month in range(1, tenure_months + 1):
            beginning_balance = current_balance
            interest_charge = round(beginning_balance * r, 2)

            if month <= moratorium_months:
                # Standard relief: interest-only servicing during moratorium
                emi_paid = interest_charge
                principal_paid = 0.0
                ending_balance = beginning_balance
            else:
                # Active amortization period
                if month == tenure_months:
                    # Final installment adjustment to eliminate roundoff residue
                    principal_paid = round(beginning_balance, 2)
                    interest_charge = round(beginning_balance * r, 2)
                    emi_paid = round(principal_paid + interest_charge, 2)
                    ending_balance = 0.0
                else:
                    emi_paid = normal_emi
                    principal_paid = round(emi_paid - interest_charge, 2)
                    if principal_paid > beginning_balance:
                        principal_paid = beginning_balance
                        emi_paid = round(principal_paid + interest_charge, 2)
                    ending_balance = round(beginning_balance - principal_paid, 2)

            schedule.append({
                "month": month,
                "beginning_balance": round(beginning_balance, 2),
                "emi": round(emi_paid, 2),
                "principal_paid": round(principal_paid, 2),
                "interest_paid": round(interest_charge, 2),
                "ending_balance": round(max(0.0, ending_balance), 2),
                "is_moratorium": month <= moratorium_months,
            })
            current_balance = ending_balance

        return pd.DataFrame(schedule)

    def optimize_restructuring(
        self,
        remaining_principal: float,
        current_emi: float,
        current_tenure_months: int,
        annual_rate: float,
        target_emi_reduction_pct: float = 0.25,
        tenure_extension_months: Optional[int] = None,
        rate_concession_bps: int = 0,
        moratorium_months: int = 0,
    ) -> Dict[str, Any]:
        """Propose an optimal restructuring package honoring customer relief targets.

        Args:
            remaining_principal: Outstanding principal amount.
            current_emi: Existing monthly EMI commitment.
            current_tenure_months: Existing remaining tenure in months.
            annual_rate: Current annual interest rate.
            target_emi_reduction_pct: Desired percentage reduction in monthly EMI.
            tenure_extension_months: Explicit tenure extension override.
            rate_concession_bps: Interest rate discount in basis points (max 200).
            moratorium_months: Grace period in months (max 6).

        Returns:
            Dictionary detailing old terms, new terms, savings, and amortization schedule.
        """
        calculate_emi(remaining_principal, annual_rate, current_tenure_months)
        number(current_emi, "current_emi", 0.01)
        number(target_emi_reduction_pct, "target_emi_reduction_pct", 0, 0.99)
        integer(rate_concession_bps, "rate_concession_bps", 0, MAX_RATE_CONCESSION_BPS)
        integer(moratorium_months, "moratorium_months", 0, MAX_MORATORIUM_MONTHS)
        applied_bps = rate_concession_bps
        restructured_rate = max(0.0, annual_rate - applied_bps / 10000)
        applied_moratorium = moratorium_months
        target_emi = round(current_emi * (1 - target_emi_reduction_pct), 2)
        if tenure_extension_months is None:
            applied_extension = MAX_TENURE_EXTENSION_MONTHS
            for ext in range(MAX_TENURE_EXTENSION_MONTHS + 1):
                active_months = current_tenure_months + ext - applied_moratorium
                if active_months > 0 and self.calculate_emi(
                    remaining_principal, restructured_rate, active_months
                ) <= target_emi:
                    applied_extension = ext
                    break
        else:
            integer(tenure_extension_months, "tenure_extension_months", 0, MAX_TENURE_EXTENSION_MONTHS)
            applied_extension = tenure_extension_months
        if current_tenure_months + applied_extension <= applied_moratorium:
            raise ValueError("At least one active repayment month is required after the moratorium")

        new_tenure = current_tenure_months + applied_extension
        new_emi = self.calculate_emi(
            remaining_principal,
            restructured_rate,
            new_tenure - applied_moratorium,
        )

        monthly_savings = current_emi - new_emi
        savings_pct = (monthly_savings / current_emi) if current_emi > 0 else 0.0

        # Generate complete amortization schedule
        schedule_df = self.generate_amortization_schedule(
            principal=remaining_principal,
            annual_rate=restructured_rate,
            tenure_months=new_tenure,
            moratorium_months=applied_moratorium,
        )

        original_schedule = self.generate_amortization_schedule(
            remaining_principal, annual_rate, current_tenure_months
        )
        total_interest_old = round(float(original_schedule["interest_paid"].sum()), 2)
        total_interest_new = round(float(schedule_df["interest_paid"].sum()), 2)

        return {
            "target_emi": target_emi,
            "target_met": new_emi <= target_emi,
            "target_status": "met" if new_emi <= target_emi else "Requested reduction is not met within these terms",
            "moratorium_payment": round(remaining_principal * restructured_rate / 12, 2) if applied_moratorium else 0.0,
            "original_schedule": original_schedule,
            "principal": remaining_principal,
            "old_tenure_months": current_tenure_months,
            "new_tenure_months": new_tenure,
            "tenure_extension_months": applied_extension,
            "old_annual_rate": annual_rate,
            "new_annual_rate": restructured_rate,
            "rate_concession_bps": round((annual_rate - restructured_rate) * 10000, 4),
            "moratorium_months": applied_moratorium,
            "old_emi": current_emi,
            "new_emi": new_emi,
            "monthly_savings": round(monthly_savings, 2),
            "savings_pct": round(savings_pct * 100, 2),
            "total_interest_old": max(0.0, total_interest_old),
            "total_interest_new": total_interest_new,
            "amortization_schedule": schedule_df,
        }
