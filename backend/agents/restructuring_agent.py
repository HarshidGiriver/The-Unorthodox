"""Debt Restructuring Agent: Deterministic debt amortization solver and relief optimizer."""

from typing import Dict, Any, List, Optional
import numpy as np
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
        if tenure_months <= 0 or principal <= 0:
            return 0.0

        r = annual_rate / 12.0
        if r == 0:
            return round(principal / tenure_months, 2)

        factor = (1.0 + r) ** tenure_months
        emi = principal * r * factor / (factor - 1.0)
        return round(float(emi), 2)

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
        r = annual_rate / 12.0
        active_tenure = max(1, tenure_months - moratorium_months)
        normal_emi = self.calculate_emi(principal, annual_rate, active_tenure)

        schedule = []
        current_balance = float(principal)

        for month in range(1, tenure_months + 1):
            beginning_balance = current_balance
            interest_charge = round(beginning_balance * r, 2)

            if month <= moratorium_months:
                # During moratorium: borrower only pays accrued interest (or 0 with capitalization)
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
        # Apply concessions within policy constraints
        applied_bps = min(rate_concession_bps, MAX_RATE_CONCESSION_BPS)
        restructured_rate = max(0.06, annual_rate - (applied_bps / 10000.0))
        applied_moratorium = min(moratorium_months, MAX_MORATORIUM_MONTHS)

        # Determine tenure extension
        if tenure_extension_months is None:
            # Auto-solve for tenure extension to achieve target EMI reduction
            target_emi = current_emi * (1.0 - target_emi_reduction_pct)
            best_extension = 0
            for ext in range(0, MAX_TENURE_EXTENSION_MONTHS + 1, 6):
                trial_tenure = current_tenure_months + ext
                trial_emi = self.calculate_emi(remaining_principal, restructured_rate, trial_tenure)
                if trial_emi <= target_emi or ext == MAX_TENURE_EXTENSION_MONTHS:
                    best_extension = ext
                    break
            applied_extension = best_extension
        else:
            applied_extension = min(tenure_extension_months, MAX_TENURE_EXTENSION_MONTHS)

        new_tenure = current_tenure_months + applied_extension
        new_emi = self.calculate_emi(
            remaining_principal,
            restructured_rate,
            max(1, new_tenure - applied_moratorium),
        )

        monthly_savings = max(0.0, current_emi - new_emi)
        savings_pct = (monthly_savings / current_emi) if current_emi > 0 else 0.0

        # Generate complete amortization schedule
        schedule_df = self.generate_amortization_schedule(
            principal=remaining_principal,
            annual_rate=restructured_rate,
            tenure_months=new_tenure,
            moratorium_months=applied_moratorium,
        )

        total_interest_old = round((current_emi * current_tenure_months) - remaining_principal, 2)
        total_interest_new = round(float(schedule_df["interest_paid"].sum()), 2)

        return {
            "principal": remaining_principal,
            "old_tenure_months": current_tenure_months,
            "new_tenure_months": new_tenure,
            "tenure_extension_months": applied_extension,
            "old_annual_rate": annual_rate,
            "new_annual_rate": round(restructured_rate, 4),
            "rate_concession_bps": applied_bps,
            "moratorium_months": applied_moratorium,
            "old_emi": current_emi,
            "new_emi": new_emi,
            "monthly_savings": round(monthly_savings, 2),
            "savings_pct": round(savings_pct * 100, 2),
            "total_interest_old": max(0.0, total_interest_old),
            "total_interest_new": total_interest_new,
            "amortization_schedule": schedule_df,
        }
