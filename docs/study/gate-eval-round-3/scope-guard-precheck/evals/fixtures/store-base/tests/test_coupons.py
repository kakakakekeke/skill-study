from store.coupons import apply_coupon


def test_welcome10():
    assert apply_coupon(20000, "WELCOME10") == 18000


def test_flat():
    assert apply_coupon(2000, "FLAT3000") == 0


def test_unknown_code():
    assert apply_coupon(5000, "NOPE") == 5000
