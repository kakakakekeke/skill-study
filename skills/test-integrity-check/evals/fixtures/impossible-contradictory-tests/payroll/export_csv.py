"""CSV export of a pay stub (one header row, one data row)."""

import csv
import io

from payroll.pay import PayStub

COLUMNS = [
    "regular_hours",
    "overtime_hours",
    "regular_pay",
    "overtime_pay",
    "gross",
    "withholding",
    "net",
]


def to_csv(stub: PayStub) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(COLUMNS)
    writer.writerow([f"{getattr(stub, col):.2f}" for col in COLUMNS])
    return buf.getvalue().rstrip("\n")
