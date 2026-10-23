from decimal import Decimal

import pytest

from ledger.discounts import apply_discounts, fixed_off, percent_off


def test_percent_off():
    assert percent_off(Decimal("200"), Decimal("10")) == Decimal("180.0")


def test_fixed_off():
    assert fixed_off(Decimal("200"), Decimal("15")) == Decimal("185")


def test_applied_in_order():
    # 10% off then 5 off: 100 -> 90 -> 85 ; 5 off then 10%: 100 -> 95 -> 85.5
    assert apply_discounts(Decimal("100"), [("percent", Decimal("10")), ("fixed", Decimal("5"))]) == Decimal("85.0")
    assert apply_discounts(Decimal("100"), [("fixed", Decimal("5")), ("percent", Decimal("10"))]) == Decimal("85.5")


def test_never_below_zero():
    assert apply_discounts(Decimal("10"), [("fixed", Decimal("50"))]) == Decimal("0")


def test_unknown_kind():
    with pytest.raises(ValueError):
        apply_discounts(Decimal("10"), [("bogus", Decimal("1"))])
