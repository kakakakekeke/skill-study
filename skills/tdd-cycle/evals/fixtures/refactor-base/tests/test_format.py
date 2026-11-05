from money import format_money


def test_krw_rounds_half_up():
    assert format_money(1234.5) == "1,235원"


def test_krw_thousands_separator():
    assert format_money(1234567) == "1,234,567원"


def test_usd_two_places():
    assert format_money(1234.567, "USD") == "$1,234.57"


def test_usd_half_up():
    assert format_money(0.125, "USD") == "$0.13"
