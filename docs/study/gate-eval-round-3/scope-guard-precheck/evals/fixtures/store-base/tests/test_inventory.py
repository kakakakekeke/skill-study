import pytest

from store.inventory import Inventory, OutOfStock


def test_take_too_many():
    inv = Inventory({"A1": "머그컵"})
    inv.add("A1", 1)
    with pytest.raises(OutOfStock):
        inv.take("A1", 2)
