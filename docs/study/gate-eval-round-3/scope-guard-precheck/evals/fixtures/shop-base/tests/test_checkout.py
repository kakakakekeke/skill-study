from shop.checkout import receipt


def test_receipt_domestic():
    r = receipt([(10000, 1)], 2, "domestic")
    assert r == {"items": "₩10,000", "shipping": "₩3,000", "total": "₩13,000"}
