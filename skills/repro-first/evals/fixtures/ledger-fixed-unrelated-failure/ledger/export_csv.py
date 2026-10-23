"""CSV export.

Header: ``sku,qty,net,tax,gross``; one row per line item; a final
``TOTAL,,,,<total>`` row. Rows are joined with ``"\\n"`` (no trailing newline).
"""

from ledger.invoice import Invoice

HEADER = "sku,qty,net,tax,gross"


def to_csv(invoice: Invoice) -> str:
    """Render ``invoice`` as CSV text."""
    rows = [HEADER]
    for item in invoice.items:
        rows.append(f"{item.sku},{item.qty},{item.net()},{item.tax()},{item.gross()}")
    rows.append(f"TOTAL,,,,{invoice.total()}")
    return "\n".join(rows)
