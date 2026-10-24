import datetime

from store.customers import is_birthday_month, loyalty_points, tier_discount


def test_gold_discount():
    assert tier_discount(10000, "gold") == 500


def test_points():
    assert loyalty_points(12500) == 12


def test_not_birthday_month():
    assert not is_birthday_month(datetime.date(1990, 3, 1), datetime.date(2026, 7, 10))
