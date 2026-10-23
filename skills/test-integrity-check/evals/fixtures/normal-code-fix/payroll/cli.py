"""CLI: ``python3 -m payroll.cli <timesheet.json>``.

Prints the CSV pay stub followed by ``Net: <amount> USD``.
"""

import json
import sys
from decimal import Decimal

from payroll.export_csv import to_csv
from payroll.money import fmt
from payroll.pay import compute_pay
from payroll.timesheet import Timesheet


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python3 -m payroll.cli <timesheet.json>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        data = json.load(fh)
    stub = compute_pay(Timesheet.from_dict(data), rate=Decimal(str(data["rate"])))
    print(to_csv(stub))
    print(f"Net: {fmt(stub.net)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
