from decimal import Decimal

from payroll.export_csv import COLUMNS, to_csv
from payroll.pay import compute_pay
from payroll.timesheet import Shift, Timesheet


def test_csv_header_and_row():
    stub = compute_pay(Timesheet([Shift("mon", Decimal("8"))]), rate=Decimal("20.00"))
    lines = to_csv(stub).split("\n")
    assert lines[0] == ",".join(COLUMNS)
    assert lines[1] == "8.00,0.00,160.00,0.00,160.00,16.00,144.00"


def test_csv_has_exactly_two_lines():
    stub = compute_pay(Timesheet([]), rate=Decimal("10.00"))
    assert len(to_csv(stub).split("\n")) == 2
