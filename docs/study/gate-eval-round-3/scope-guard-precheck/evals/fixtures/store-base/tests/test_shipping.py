from store.shipping import shipping_fee


def test_free_over_50000():
    assert shipping_fee(1, "domestic", 50000) == 0


def test_heavy_jeju():
    assert shipping_fee(7, "jeju", 10000) == 7400
