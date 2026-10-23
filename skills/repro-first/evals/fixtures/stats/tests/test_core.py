import pytest
from statkit import mean, median, variance


def test_mean():
    assert mean([1, 2, 3]) == 2


def test_mean_empty():
    with pytest.raises(ValueError):
        mean([])


def test_variance():
    assert variance([2, 4, 4, 4, 5, 5, 7, 9]) == 4


def test_median_odd():
    assert median([3, 1, 2]) == 2


def test_median_single():
    assert median([5]) == 5
