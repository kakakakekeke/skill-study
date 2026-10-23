from decimal import Decimal

from ledger import Invoice, LineItem
from ledger.export_csv import to_csv


def _inv():
    return Invoice([
        LineItem("A", Decimal("10.00"), 1, Decimal("0.1")),
        LineItem("B", Decimal("2.50"), 2),
    ])


def test_header_and_rows():
    lines = to_csv(_inv()).split("\n")
    assert lines[0] == "sku,qty,net,tax,gross"
    assert lines[1] == "A,1,10.00,1.00,11.00"
    assert lines[2] == "B,2,5.00,0.00,5.00"


def test_total_row_last():
    assert to_csv(_inv()).split("\n")[-1] == "TOTAL,,,,16.00"
