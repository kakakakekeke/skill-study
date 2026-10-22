import logging
import pytest
from calc import parse_range, format_money, split_csv, mean, clamp, percent, to_cents

log = logging.getLogger("calc.tests")


def _chatter(n=40):
    # 실제 서비스 테스트처럼 로그를 많이 찍는다 (실패 시 캡처 출력으로 노출)
    for i in range(n):
        print(f"[fixture] loading tariff row {i:03d} region=eu-west-{i % 3} status=ok latency={3.1 + i * 0.07:.2f}ms")
        log.info("processed row %d", i)


@pytest.mark.parametrize("spec,expected", [("4", [4]), ("0", [0]), ("10", [10])])
def test_parse_single(spec, expected):
    _chatter(5)
    assert parse_range(spec) == expected


def test_parse_range_inclusive():
    _chatter()
    assert parse_range("3-6") == [3, 4, 5, 6]


def test_parse_range_same_bounds():
    _chatter()
    assert parse_range("7-7") == [7]


@pytest.mark.parametrize("amount,expected", [("3", "$3.00"), (2.5, "$2.50"), (Decimal := 10, "$10.00")])
def test_format_money_usd(amount, expected):
    _chatter(3)
    assert format_money(amount) == expected


def test_format_money_eur():
    assert format_money(4, "EUR") == "4.00 EUR"


def test_format_money_none():
    _chatter()
    assert format_money(None) == "$0.00"


@pytest.mark.parametrize("line", ["a,b", " a , b ", "a,,b", "x"])
def test_split_csv(line):
    assert all(isinstance(p, str) for p in split_csv(line))


def test_mean():
    assert mean([1, 2, 3]) == 2
    assert mean([]) == 0.0


@pytest.mark.parametrize("x,lo,hi,exp", [(5, 0, 10, 5), (-1, 0, 10, 0), (11, 0, 10, 10)])
def test_clamp(x, lo, hi, exp):
    assert clamp(x, lo, hi) == exp


@pytest.mark.parametrize("part,whole,exp", [(1, 4, 25.0), (0, 4, 0.0), (3, 0, 0.0), (2, 8, 25.0), (5, 5, 100.0)])
def test_percent(part, whole, exp):
    assert percent(part, whole) == exp


@pytest.mark.parametrize("amt,exp", [("1.23", 123), (0.1, 10), (19.99, 1999), ("0", 0)])
def test_to_cents(amt, exp):
    assert to_cents(amt) == exp
