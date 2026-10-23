from decimal import Decimal

from payroll.tax import DEFAULT_BRACKETS, Bracket, rate_for, withhold


def test_rate_for_lowest_bracket():
    assert rate_for(Decimal("0.00")) == Decimal("0.10")
    assert rate_for(Decimal("250.00")) == Decimal("0.10")


def test_bracket_boundary():
    # upper bounds are inclusive (README): exactly 500.00 is still 10%
    assert rate_for(Decimal("500.00")) == Decimal("0.10")
    assert rate_for(Decimal("500.01")) == Decimal("0.20")
    assert rate_for(Decimal("1500.00")) == Decimal("0.20")
    assert rate_for(Decimal("1500.01")) == Decimal("0.30")


def test_rate_for_top_bracket():
    assert rate_for(Decimal("9999.00")) == Decimal("0.30")


def test_withhold_and_custom_table():
    assert withhold(Decimal("400.00")) == Decimal("40.00")
    assert withhold(Decimal("1000.00")) == Decimal("200.00")
    flat = [Bracket(None, Decimal("0.25"))]
    assert withhold(Decimal("100.00"), flat) == Decimal("25.00")
    assert len(DEFAULT_BRACKETS) == 3
