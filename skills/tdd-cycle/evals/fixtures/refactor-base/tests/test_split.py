import pytest

from money import split_bill


def test_even_split():
    assert split_bill(100, 4) == [25.0, 25.0, 25.0, 25.0]


def test_remainder_goes_first():
    assert split_bill(100, 3) == [33.34, 33.33, 33.33]


def test_sum_matches_total():
    assert round(sum(split_bill(10, 3)), 2) == 10.0


def test_invalid_n():
    with pytest.raises(ValueError):
        split_bill(10, 0)
