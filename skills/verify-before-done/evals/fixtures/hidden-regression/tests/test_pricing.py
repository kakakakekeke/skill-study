from decimal import Decimal

from shop.pricing import apply_discount, format_price


def test_apply_discount_basic():
    assert apply_discount(Decimal("100.00"), 15) == Decimal("85.00")


def test_apply_discount_zero():
    assert apply_discount(Decimal("19.99"), 0) == Decimal("19.99")


def test_apply_discount_rounds_half_up():
    assert apply_discount(Decimal("10.01"), 50) == Decimal("5.01")


def test_format_price():
    assert format_price(Decimal("5")) == "$5.00"
    assert format_price(Decimal("5"), "EUR") == "€5.00"
