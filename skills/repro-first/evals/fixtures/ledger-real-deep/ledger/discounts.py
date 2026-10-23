"""Discounts.

A discount is a ``(kind, value)`` tuple where ``kind`` is ``"percent"`` or
``"fixed"``. Discounts are applied in order; the result is never below 0.
Intermediate results are *not* rounded; rounding happens once per line in
``ledger.invoice``.
"""

from decimal import ROUND_DOWN, Decimal

Discount = tuple[str, Decimal]

CENT = Decimal("0.01")


def percent_off(amount: Decimal, pct: Decimal) -> Decimal:
    """Reduce ``amount`` by ``pct`` percent (``Decimal("10")`` = 10%)."""
    return (Decimal(amount) * (1 - Decimal(pct) / 100)).quantize(CENT, rounding=ROUND_DOWN)


def fixed_off(amount: Decimal, value: Decimal) -> Decimal:
    """Reduce ``amount`` by a fixed ``value``."""
    return Decimal(amount) - Decimal(value)


def apply_discounts(amount: Decimal, discounts: list[Discount]) -> Decimal:
    """Apply ``discounts`` to ``amount`` in order; never return less than 0."""
    result = Decimal(amount)
    for kind, value in discounts:
        if kind == "percent":
            result = percent_off(result, value)
        elif kind == "fixed":
            result = fixed_off(result, value)
        else:
            raise ValueError(f"unknown discount kind: {kind!r}")
    return max(result, Decimal("0"))
