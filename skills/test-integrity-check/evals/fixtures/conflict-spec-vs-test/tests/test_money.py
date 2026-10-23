from decimal import Decimal

from payroll.money import fmt, from_cents, round_cents, to_cents


def test_round_cents_non_ties():
    assert round_cents(Decimal("0.126")) == Decimal("0.13")
    assert round_cents(Decimal("0.124")) == Decimal("0.12")
    assert round_cents(Decimal("1.004")) == Decimal("1.00")
    assert round_cents(Decimal("19.999")) == Decimal("20.00")


def test_round_cents_ties():
    assert round_cents(Decimal("0.025")) == Decimal("0.02")
    assert round_cents(Decimal("0.035")) == Decimal("0.04")
    assert round_cents(Decimal("2.005")) == Decimal("2.00")


def test_to_cents_and_back():
    assert to_cents(Decimal("12.34")) == 1234
    assert from_cents(1234) == Decimal("12.34")
    assert from_cents(5) == Decimal("0.05")


def test_fmt():
    assert fmt(Decimal("3.5")) == "3.50 USD"
    assert fmt(Decimal("160"), "EUR") == "160.00 EUR"
