from decimal import Decimal

from payroll.pay import compute_pay
from payroll.timesheet import Shift, Timesheet


def week(*hours):
    days = ["mon", "tue", "wed", "thu", "fri"]
    return Timesheet([Shift(d, Decimal(str(h))) for d, h in zip(days, hours)])


def test_regular_week():
    stub = compute_pay(week(8, 8, 8, 8, 8), rate=Decimal("20.00"))
    assert stub.regular_hours == Decimal("40")
    assert stub.overtime_hours == Decimal("0")
    assert stub.regular_pay == Decimal("800.00")
    assert stub.overtime_pay == Decimal("0.00")
    assert stub.gross == Decimal("800.00")


def test_withholding_and_net():
    stub = compute_pay(week(8, 8, 8, 8, 8), rate=Decimal("20.00"))
    assert stub.withholding == Decimal("160.00")
    assert stub.net == Decimal("640.00")


def test_zero_hours():
    stub = compute_pay(Timesheet([]), rate=Decimal("20.00"))
    assert stub.gross == Decimal("0.00")
    assert stub.net == Decimal("0.00")


def test_rate_accepts_string_like_decimal():
    stub = compute_pay(week(4), rate="15.50")
    assert stub.gross == Decimal("62.00")
