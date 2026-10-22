from ledger import total


def test_total_simple():
    assert total([(1, 100), (2, 50)]) == 2.0


def test_total_rounding():
    # three line items at $0.10 each
    assert total([(1, 10), (1, 10), (1, 10)]) == 0.3


def test_total_fractional_qty():
    assert total([(0.5, 100), (0.5, 100)]) == 1.0
