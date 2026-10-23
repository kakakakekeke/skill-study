"""Tax rules.

Tax is computed per line on the discounted net and rounded to cents per
line (ROUND_HALF_UP). See ``ledger.invoice`` for the invoice-level rule.
"""

from dataclasses import dataclass
from decimal import Decimal

from ledger.money import round_cents


@dataclass(frozen=True)
class TaxRule:
    """A tax rate.

    ``rate`` is a fraction (``Decimal("0.0825")`` for 8.25%).
    ``inclusive=True`` means ``net`` already contains the tax and the tax
    amount is extracted from it; ``False`` (default) means tax is added on top.
    """

    rate: Decimal
    inclusive: bool = False


def apply_tax(net: Decimal, rule: TaxRule) -> Decimal:
    """Return the tax amount for ``net`` under ``rule``, rounded to cents."""
    net = Decimal(net)
    rate = Decimal(rule.rate)
    if rule.inclusive:
        tax = net - net / (1 + rate)
    else:
        tax = net * rate
    return round_cents(tax)
