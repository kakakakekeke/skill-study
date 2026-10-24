from decimal import Decimal

from shop.pricing import apply_discount, line_total, order_total


def test_line_total_rounds_half_up():
    assert line_total("0.125", 1) == Decimal("0.13")


def test_discount_basic():
    assert apply_discount(1000, 10) == Decimal("900.00")


def test_order_total():
    assert order_total([(1000, 2), (500, 1)], 10) == Decimal("2250.00")
