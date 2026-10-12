"""Finance calculators used to verify every computed number in a script.

Scripts declare claims like ``{calc: doubling_years, args: {rate: 0.08}, expect: 9.0}``;
``verify_claim`` recomputes the value so a wrong number never reaches a video.
"""

from __future__ import annotations

import math


def future_value(principal: float = 0.0, rate: float = 0.0, years: float = 0.0,
                 monthly_contribution: float = 0.0, periods_per_year: int = 12) -> float:
    """Value after compounding `principal` plus end-of-period contributions."""
    n = periods_per_year
    r = rate / n
    periods = round(years * n)
    contribution = monthly_contribution * 12 / n
    if r == 0:
        return principal + contribution * periods
    growth = (1 + r) ** periods
    return principal * growth + contribution * (growth - 1) / r


def total_contributed(principal: float = 0.0, years: float = 0.0,
                      monthly_contribution: float = 0.0) -> float:
    return principal + monthly_contribution * 12 * years


def doubling_years(rate: float) -> float:
    """Exact years to double at an annual compound rate."""
    return math.log(2) / math.log(1 + rate)


def rule_of_72(rate: float) -> float:
    """Rule-of-72 estimate; `rate` is a fraction (0.08 = 8 %)."""
    return 72 / (rate * 100)


def real_value(amount: float, inflation: float, years: float) -> float:
    """Purchasing power of `amount` after `years` of constant inflation."""
    return amount / (1 + inflation) ** years


def loan_payment(principal: float, apr: float, months: int) -> float:
    """Fixed monthly payment for an amortising loan."""
    r = apr / 12
    if r == 0:
        return principal / months
    return principal * r / (1 - (1 + r) ** -months)


def payoff_months(balance: float, apr: float, monthly_payment: float) -> float:
    """Months to clear a balance with a fixed payment (inf if never)."""
    r = apr / 12
    if r == 0:
        return math.ceil(balance / monthly_payment)
    if monthly_payment <= balance * r:
        return math.inf
    return math.ceil(-math.log(1 - balance * r / monthly_payment) / math.log(1 + r))


def payoff_interest(balance: float, apr: float, monthly_payment: float) -> float:
    """Total interest paid when clearing a balance with a fixed payment."""
    r = apr / 12
    remaining, paid, months = balance, 0.0, 0
    while remaining > 0.005:
        months += 1
        if months > 1200:
            return math.inf
        remaining *= 1 + r
        pay = min(monthly_payment, remaining)
        remaining -= pay
        paid += pay
    return paid - balance


def remaining_balance(balance: float, apr: float, monthly_payment: float, months: float) -> float:
    """Balance left after `months` fixed payments (never below zero)."""
    r = apr / 12
    remaining = balance
    for _ in range(int(round(months))):
        remaining = remaining * (1 + r) - monthly_payment
        if remaining <= 0:
            return 0.0
    return remaining


def effective_annual_rate(apr: float, periods_per_year: int = 12) -> float:
    return (1 + apr / periods_per_year) ** periods_per_year - 1


def percent_change(old: float, new: float) -> float:
    return (new - old) / old


def combinations(n: int, k: int) -> int:
    return math.comb(n, k)


def odds_one_in(n: int, k: int, bonus_pool: int = 1) -> int:
    """Lottery-style odds: pick k of n, times an optional bonus ball pool."""
    return math.comb(n, k) * bonus_pool


def expected_value(outcomes: list) -> float:
    """`outcomes` is a list of [probability, payoff] pairs."""
    return sum(p * v for p, v in outcomes)


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    return a / b


CALCULATORS = {
    "future_value": future_value,
    "total_contributed": total_contributed,
    "doubling_years": doubling_years,
    "rule_of_72": rule_of_72,
    "real_value": real_value,
    "loan_payment": loan_payment,
    "payoff_months": payoff_months,
    "payoff_interest": payoff_interest,
    "remaining_balance": remaining_balance,
    "effective_annual_rate": effective_annual_rate,
    "percent_change": percent_change,
    "combinations": combinations,
    "odds_one_in": odds_one_in,
    "expected_value": expected_value,
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}


def verify_claim(check: dict) -> tuple[bool, float, str]:
    """Recompute a claim. Returns (ok, actual, message).

    `tolerance` is relative (default 2 %), so a script may round 10.24 to "about 10".
    """
    name = check.get("calc")
    fn = CALCULATORS.get(name)
    if fn is None:
        return False, math.nan, f"unknown calculator {name!r}; known: {', '.join(sorted(CALCULATORS))}"
    try:
        actual = float(fn(**(check.get("args") or {})))
    except TypeError as e:
        return False, math.nan, f"bad args for {name}: {e}"
    expect = float(check["expect"])
    tol = float(check.get("tolerance", 0.02))
    if math.isinf(actual) or math.isinf(expect):
        ok = actual == expect
    elif expect == 0:
        ok = abs(actual) <= tol
    else:
        ok = abs(actual - expect) / abs(expect) <= tol
    msg = f"{name}({check.get('args')}) = {actual:,.4f}, script says {expect:,.4f} (tolerance {tol:.0%})"
    return ok, actual, msg
