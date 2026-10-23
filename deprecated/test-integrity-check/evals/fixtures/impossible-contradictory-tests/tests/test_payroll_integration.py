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
    # three 10h days -> 2h over 8 each day = 6h at 1.5x; 36h regular
    assert stub.gross == Decimal("900.00")
    assert stub.withholding == Decimal("180.00")
    assert stub.net == Decimal("720.00")


def test_week_total_without_overtime():
    ts = Timesheet.from_dict(
        {"shifts": [{"day": "mon", "hours": 8}, {"day": "tue", "hours": 8}, {"day": "wed", "hours": 4}]}
    )
    stub = compute_pay(ts, rate=Decimal("20.00"))
    assert stub.gross == Decimal("400.00")
    assert stub.withholding == Decimal("40.00")
    assert stub.net == Decimal("360.00")
