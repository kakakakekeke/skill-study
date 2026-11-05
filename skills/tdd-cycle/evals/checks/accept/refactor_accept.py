"""refactor-base 동작 보존 수용 테스트. 모델에게 보이지 않는다. 정리 전 참조 구현으로 통과를 확인했다."""
from money import apply_tax, format_money, split_bill
import pytest


@pytest.mark.parametrize("amount,expected", [(1234.5, "1,235원"), (0.5, "1원"), (2.5, "3원"), (1234567, "1,234,567원"), (0, "0원")])
def test_krw(amount, expected):
    assert format_money(amount) == expected


@pytest.mark.parametrize("amount,expected", [(1234.567, "$1,234.57"), (0.125, "$0.13"), (0.005, "$0.01"), (1000, "$1,000.00")])
def test_usd(amount, expected):
    assert format_money(amount, "USD") == expected


def test_unknown_currency():
    with pytest.raises(ValueError):
        format_money(1, "EUR")


@pytest.mark.parametrize("amount,rate,expected", [(100, 0.1, 110.0), (10.05, 0.1, 11.06), (99.99, 0, 99.99), (0.005, 0, 0.01), (1, 0.075, 1.08)])
def test_tax(amount, rate, expected):
    assert apply_tax(amount, rate) == expected


@pytest.mark.parametrize("total,n,expected", [(100, 4, [25.0] * 4), (100, 3, [33.34, 33.33, 33.33]), (10, 3, [3.34, 3.33, 3.33]), (0.01, 2, [0.0, 0.01])])
def test_split(total, n, expected):
    assert split_bill(total, n) == expected


def test_split_invalid():
    with pytest.raises(ValueError):
        split_bill(10, 0)
