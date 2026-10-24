from store.pricing import subtotal


def test_subtotal():
    assert subtotal([(1200, 2), (990, 3)]) == 5370
