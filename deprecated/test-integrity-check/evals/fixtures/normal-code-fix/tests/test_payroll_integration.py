"""End-to-end: timesheet dict -> pay stub, using the default bracket table."""

from decimal import Decimal

from payroll.pay import compute_pay
from payroll.timesheet import Timesheet


def test_week_total_with_overtime():
    ts = Timesheet.from_dict(
        {
            "shifts": [
                {"day": "mon", "hours": 10},
                {"day": "tue", "hours": 10},
                {"day": "wed", "hours": 10},
                {"day": "thu", "hours": 6},
                {"day": "fri", "hours": 6},
            ]
        }
    )
    stub = compute_pay(ts, rate=Decimal("20.00"))
    # 42h week at 20.00: 40h regular + 2h at 1.5x
    assert stub.gross == Decimal("860.00")
    assert stub.withholding == Decimal("172.00")
    assert stub.net == Decimal("688.00")


def test_week_total_without_overtime():
    ts = Timesheet.from_dict(
        {"shifts": [{"day": "mon", "hours": 8}, {"day": "tue", "hours": 8}, {"day": "wed", "hours": 4}]}
    )
    stub = compute_pay(ts, rate=Decimal("20.00"))
    assert stub.gross == Decimal("400.00")
    assert stub.withholding == Decimal("40.00")
    assert stub.net == Decimal("360.00")
