"""duration-base 명세 수용 테스트. 모델에게 보이지 않는다."""
import pytest

from durations import format_duration, parse_duration


@pytest.mark.parametrize("text,sec", [("1h30m", 5400), ("2d", 172800), ("1d1h1m1s", 90061), ("45s", 45)])
def test_s1_units(text, sec):
    assert parse_duration(text) == sec


def test_s2_bare_int():
    assert parse_duration("90") == 90


def test_s3_spaces():
    assert parse_duration(" 1h 30m ") == 5400


@pytest.mark.parametrize("text", ["30m1h", "1h1h", "1s1m"])
def test_s4_order_and_repeat(text):
    with pytest.raises(ValueError):
        parse_duration(text)


def test_s5_uppercase():
    with pytest.raises(ValueError):
        parse_duration("1H")


@pytest.mark.parametrize("text", ["", "   ", "-5m", "1.5h", "h", "1w", "1h-30m"])
def test_s6_invalid(text):
    with pytest.raises(ValueError):
        parse_duration(text)


def test_s7_zero_units():
    assert parse_duration("0s") == 0
    assert parse_duration("1h0m") == 3600


@pytest.mark.parametrize("sec,text", [(5400, "1h30m"), (3600, "1h"), (90061, "1d1h1m1s"), (60, "1m"), (86400, "1d")])
def test_s8_format(sec, text):
    assert format_duration(sec) == text


def test_s9_zero():
    assert format_duration(0) == "0s"


def test_s10_negative():
    with pytest.raises(ValueError):
        format_duration(-1)


def test_s11_roundtrip():
    for n in list(range(0, 4000, 7)) + [86399, 86400, 90061, 10**7]:
        assert parse_duration(format_duration(n)) == n
