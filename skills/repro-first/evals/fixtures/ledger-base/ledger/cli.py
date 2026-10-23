"""CLI: ``python3 -m ledger.cli <invoice.json>``.

Prints the CSV export followed by ``Total: <amount> <currency>``.
"""

import json
import sys

from ledger.export_csv import to_csv
from ledger.invoice import Invoice
from ledger.money import fmt


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python3 -m ledger.cli <invoice.json>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        data = json.load(fh)
    invoice = Invoice.from_dict(data)
    print(to_csv(invoice))
    print(f"Total: {fmt(invoice.total(), invoice.currency)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
