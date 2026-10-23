from decimal import Decimal

from ledger.tax import TaxRule, apply_tax


def test_exclusive_tax_rounded():
    assert apply_tax(Decimal("100.00"), TaxRule(Decimal("0.0825"))) == Decimal("8.25")
    assert apply_tax(Decimal("19.99"), TaxRule(Decimal("0.0825"))) == Decimal("1.65")


def test_inclusive_tax_extracted():
    assert apply_tax(Decimal("108.25"), TaxRule(Decimal("0.0825"), inclusive=True)) == Decimal("8.25")


def test_zero_rate():
    assert apply_tax(Decimal("50.00"), TaxRule(Decimal("0"))) == Decimal("0.00")
