from money import apply_tax


def test_default_rate():
    assert apply_tax(100) == 110.0


def test_rounds_half_up():
    assert apply_tax(10.05, 0.1) == 11.06


def test_zero_rate():
    assert apply_tax(99.99, 0) == 99.99
