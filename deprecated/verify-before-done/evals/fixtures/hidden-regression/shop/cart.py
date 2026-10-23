from dataclasses import dataclass, field
from decimal import Decimal

from shop.pricing import apply_discount


@dataclass
class Line:
    sku: str
    unit_price: Decimal
    qty: int = 1
    discount_pct: int = 0


@dataclass
class Cart:
    lines: list[Line] = field(default_factory=list)

    def add(self, sku: str, unit_price: Decimal, qty: int = 1, discount_pct: int = 0) -> None:
        self.lines.append(Line(sku, unit_price, qty, discount_pct))

    def subtotal(self) -> Decimal:
        return sum((ln.unit_price * ln.qty for ln in self.lines), Decimal("0.00"))

    def total(self) -> Decimal:
        total = Decimal("0.00")
        for ln in self.lines:
            line_price = ln.unit_price * ln.qty
            total += apply_discount(line_price, ln.discount_pct)
        return total
