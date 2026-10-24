from store.tax import vat


def test_vat_rounds_half_up():
    assert vat(15) == 2
