"""Withholding table.

A flat rate is looked up by weekly gross. Bracket upper bounds are
*inclusive*: a gross exactly equal to ``upper`` belongs to that bracket.
"""

from dataclasses import dataclass
from decimal import Decimal

from payroll.money import round_cents


@dataclass(frozen=True)
class Bracket:
    """``upper`` is the inclusive top of the bracket; ``None`` means open-ended."""

    upper: Decimal | None
    rate: Decimal


DEFAULT_BRACKETS: list[Bracket] = [
    Bracket(Decimal("500.00"), Decimal("0.10")),
    Bracket(Decimal("1500.00"), Decimal("0.20")),
    Bracket(None, Decimal("0.30")),
]


def rate_for(gross: Decimal, brackets: list[Bracket] = DEFAULT_BRACKETS) -> Decimal:
    """Return the withholding rate for ``gross``."""
    for bracket in brackets:
        if bracket.upper is None or gross < bracket.upper:
            return bracket.rate
    raise ValueError("bracket table must end with an open-ended bracket")


def withhold(gross: Decimal, brackets: list[Bracket] = DEFAULT_BRACKETS) -> Decimal:
    """Withholding amount for ``gross``, rounded to cents."""
    return round_cents(Decimal(gross) * rate_for(gross, brackets))
