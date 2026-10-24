from decimal import Decimal

from payroll.timesheet import Shift, Timesheet


def week(*hours):
    days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    return Timesheet([Shift(d, Decimal(str(h))) for d, h in zip(days, hours)])


def test_total_hours():
    assert week(8, 8, 8, 8, 6).total_hours() == Decimal("38")
    assert Timesheet([]).total_hours() == Decimal("0")


def test_no_overtime_at_or_under_40():
    assert week(8, 8, 8, 8, 8).split_hours() == (Decimal("40"), Decimal("0"))
    assert week(10, 10, 10, 8).split_hours() == (Decimal("38"), Decimal("0"))


def test_weekly_overtime_split():
    # 10+10+10+6+6 = 42h in the week -> 40 regular, 2 overtime
    assert week(10, 10, 10, 6, 6).split_hours() == (Decimal("40"), Decimal("2"))


def test_from_dict():
    ts = Timesheet.from_dict({"shifts": [{"day": "mon", "hours": 7.5}, {"day": "tue", "hours": 8}]})
    assert ts.shifts[0] == Shift("mon", Decimal("7.5"))
    assert ts.total_hours() == Decimal("15.5")
