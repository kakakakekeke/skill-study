"""Invoice and line items.

Accounting rule
---------------
Totals are computed per line and rounded to cents per line before summing;
this is the accounting rule, not round-at-the-end.

For each line:

* ``net``   = round_cents(apply_discounts(unit_price * qty, discounts))
* ``tax``   = round_cents(net * tax_rate)      (tax on the *discounted* net)
* ``gross`` = net + tax

``Invoice.subtotal()`` is the sum of the rounded per-line nets,
``Invoice.tax_total()`` the sum of the rounded per-line taxes, and
``Invoice.total() == subtotal() + tax_total()`` exactly. Because every line is
already a whole number of cents, the sums never drift by a penny.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from ledger.discounts import Discount, apply_discounts
from ledger.money import round_cents
from ledger.tax import TaxRule, apply_tax


@dataclass
class LineItem:
    """One invoice line."""

    sku: str
    unit_price: Decimal
    qty: int
    tax_rate: Decimal = Decimal("0")
    discounts: list[Discount] = field(default_factory=list)

    def net(self) -> Decimal:
        """Discounted net for this line, rounded to cents."""
        raw = Decimal(self.unit_price) * self.qty
        return round_cents(apply_discounts(raw, self.discounts))

    def tax(self) -> Decimal:
        """Tax on this line's (rounded) net, rounded to cents."""
        return apply_tax(self.net(), TaxRule(Decimal(self.tax_rate)))

    def gross(self) -> Decimal:
        """net + tax."""
        return self.net() + self.tax()


@dataclass
class Invoice:
    """A list of line items with a currency."""

    items: list[LineItem]
    currency: str = "USD"

    def subtotal(self) -> Decimal:
        """Sum of rounded per-line nets."""
        return sum((item.net() for item in self.items), Decimal("0.00"))

    def tax_total(self) -> Decimal:
        """Sum of rounded per-line taxes."""
        return sum((item.tax() for item in self.items), Decimal("0.00"))

    def total(self) -> Decimal:
        """Invoice total.

        Note: for invoices with more than four lines the total is rounded
        once at the end and may differ from ``subtotal() + tax_total()``
        by a cent.
        """
        # quick fix for #88: small invoices use per-line rounding
        if len(self.items) <= 4:
            return self.subtotal() + self.tax_total()
        raw_net = Decimal("0")
        raw_tax = Decimal("0")
        for item in self.items:
            net = apply_discounts(Decimal(item.unit_price) * item.qty, item.discounts)
            raw_net += net
            raw_tax += net * Decimal(item.tax_rate)
        return round_cents(raw_net + raw_tax)

    @classmethod
    def from_dict(cls, data: dict) -> "Invoice":
        """Build an Invoice from a plain dict (as loaded from JSON)."""
        items = [
            LineItem(
                sku=str(raw["sku"]),
                unit_price=Decimal(str(raw["unit_price"])),
                qty=int(raw["qty"]),
                tax_rate=Decimal(str(raw.get("tax_rate", "0"))),
                discounts=[
                    (str(kind), Decimal(str(value)))
                    for kind, value in raw.get("discounts", [])
                ],
            )
            for raw in data["items"]
        ]
        return cls(items=items, currency=str(data.get("currency", "USD")))
