from decimal import Decimal

from ledger import Invoice, LineItem

RATE = Decimal("0.0825")


def test_line_net_tax_gross():
    item = LineItem("A", Decimal("19.99"), 3, RATE)
    assert item.net() == Decimal("59.97")
    assert item.tax() == Decimal("4.95")
    assert item.gross() == Decimal("64.92")


def test_tax_on_discounted_net():
    item = LineItem("B", Decimal("4.50"), 7, RATE, [("percent", Decimal("10"))])
    assert item.net() == Decimal("28.35")
    assert item.tax() == Decimal("2.34")


def test_total_is_subtotal_plus_tax_total():
    inv = Invoice([
        LineItem("A", Decimal("19.99"), 3, RATE),
        LineItem("B", Decimal("4.50"), 7, RATE, [("percent", Decimal("10"))]),
        LineItem("C", Decimal("129.00"), 1, RATE),
        LineItem("D", Decimal("2.375"), 2, RATE),
    ])
    assert inv.total() == inv.subtotal() + inv.tax_total()


def test_per_line_rounding_no_penny_drift():
    # Five taxed lines: per-line rounding must be used, not round-at-the-end.
    inv = Invoice([LineItem(f"S{i}", Decimal("0.333"), 1, RATE) for i in range(5)])
    assert inv.subtotal() == Decimal("1.65")
    assert inv.tax_total() == Decimal("0.15")
    assert inv.total() == Decimal("1.80")


def test_from_dict():
    inv = Invoice.from_dict({
        "currency": "EUR",
        "items": [{"sku": "X", "unit_price": "1.00", "qty": 2, "discounts": [["fixed", "0.5"]]}],
    })
    assert inv.currency == "EUR"
    assert inv.items[0].discounts == [("fixed", Decimal("0.5"))]
    assert inv.total() == Decimal("1.50")
