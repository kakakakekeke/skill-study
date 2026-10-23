"""Money helpers.

All amounts are ``Decimal``. Rounding is always ``ROUND_HALF_UP`` to 0.01
(so 0.025 -> 0.03, 0.035 -> 0.04), never banker's rounding.
"""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def round_cents(amount: Decimal) -> Decimal:
    """Round ``amount`` to whole cents using ROUND_HALF_UP."""
    return Decimal(amount).quantize(CENT, rounding=ROUND_HALF_UP)


def to_cents(amount: Decimal) -> int:
    """Convert a decimal amount to an integer number of cents."""
    return int(round_cents(amount) * 100)


def from_cents(cents: int) -> Decimal:
    """Convert an integer number of cents to a Decimal amount."""
    return (Decimal(int(cents)) / 100).quantize(CENT)


def fmt(amount: Decimal, currency: str = "USD") -> str:
    """Format an amount as ``'12.34 USD'`` (rounded to cents)."""
    return f"{round_cents(amount):.2f} {currency}"
