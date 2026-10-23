from decimal import Decimal

from shop import Cart


def test_total_with_line_discount():
    c = Cart()
    c.add("A", Decimal("20.00"), qty=2, discount_pct=10)
    c.add("B", Decimal("5.00"))
    assert c.subtotal() == Decimal("45.00")
    assert c.total() == Decimal("41.00")


def test_total_empty():
    assert Cart().total() == Decimal("0.00")
