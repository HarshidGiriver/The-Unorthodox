"""Shared loan arithmetic and input contracts (amounts in INR, APR as a fraction)."""

import math
from numbers import Integral, Real


def number(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside the allowed range")
    return value


def integer(value, name, minimum=0, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise ValueError(f"{name} must be an integer")
    return number(value, name, minimum, maximum)


def calculate_emi(principal, annual_rate, tenure_months):
    number(principal, "principal", 0.01)
    number(annual_rate, "annual_rate", 0, 1)
    integer(tenure_months, "tenure_months", 1, 1200)
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return round(principal / tenure_months, 2)
    return round(principal * monthly_rate / -math.expm1(-tenure_months * math.log1p(monthly_rate)), 2)


BASELINE_PRINCIPAL = 300000.0
BASELINE_RATE = 0.14
BASELINE_TENURE = 24
BASELINE_EMI = calculate_emi(BASELINE_PRINCIPAL, BASELINE_RATE, BASELINE_TENURE)
