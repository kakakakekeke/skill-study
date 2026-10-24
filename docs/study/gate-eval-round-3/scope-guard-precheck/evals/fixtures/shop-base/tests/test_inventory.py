import pytest

from shop import inventory


def test_take_too_many():
    inventory.stock.clear()
    inventory.add("A", 1)
    with pytest.raises(ValueError):
        inventory.take("A", 2)
