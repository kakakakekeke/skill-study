from decimal import Decimal

from shop.promo import promo_price


def test_promo_known_code():
    assert promo_price(Decimal("40.00"), "summer25") == Decimal("30.00")


def test_promo_unknown_code():
    assert promo_price(Decimal("40.00"), "NOPE") == Decimal("40.00")
