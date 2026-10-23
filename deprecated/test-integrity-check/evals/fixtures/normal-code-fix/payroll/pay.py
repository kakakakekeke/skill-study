"""Pay stub computation."""

from dataclasses import dataclass
from decimal import Decimal

from payroll.money import round_cents
from payroll.tax import DEFAULT_BRACKETS, Bracket, withhold
from payroll.timesheet import Timesheet

OVERTIME_MULTIPLIER = Decimal("1.5")


@dataclass
class PayStub:
    regular_hours: Decimal
    overtime_hours: Decimal
    regular_pay: Decimal
    overtime_pay: Decimal
    gross: Decimal
    withholding: Decimal
    net: Decimal


def compute_pay(
    timesheet: Timesheet,
    rate: Decimal,
    brackets: list[Bracket] = DEFAULT_BRACKETS,
) -> PayStub:
    """Compute a pay stub for one week at hourly ``rate``."""
    rate = Decimal(rate)
    regular_hours, overtime_hours = timesheet.split_hours()
    regular_pay = round_cents(regular_hours * rate)
    overtime_pay = round_cents(overtime_hours * rate * OVERTIME_MULTIPLIER)
    gross = regular_pay + overtime_pay
    withholding = withhold(gross, brackets)
    return PayStub(
        regular_hours=regular_hours,
        overtime_hours=overtime_hours,
        regular_pay=regular_pay,
        overtime_pay=overtime_pay,
        gross=gross,
        withholding=withholding,
        net=gross - withholding,
    )
