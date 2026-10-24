from store.receipt import build_receipt


def test_basic_receipt():
    r = build_receipt([(10000, 2)], "domestic", 1)
    assert r == {"items": 20000, "discounted": 20000, "vat": 2000, "shipping": 3000, "total": 25000}
