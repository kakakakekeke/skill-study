from decimal import Decimal

from ledger.money import fmt, from_cents, round_cents, to_cents


def test_round_half_up():
    assert round_cents(Decimal("0.005")) == Decimal("0.01")
    assert round_cents(Decimal("0.125")) == Decimal("0.13")
    assert round_cents(Decimal("1.004")) == Decimal("1.00")


def test_to_cents_and_back():
    assert to_cents(Decimal("12.34")) == 1234
    assert from_cents(1234) == Decimal("12.34")
    assert from_cents(5) == Decimal("0.05")


def test_fmt():
    assert fmt(Decimal("3.5")) == "3.50 USD"
    assert fmt(Decimal("3.555"), "EUR") == "3.56 EUR"
