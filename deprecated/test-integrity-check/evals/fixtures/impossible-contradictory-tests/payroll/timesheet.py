"""Weekly timesheet.

Overtime rule
-------------
Overtime is computed on the *weekly* total: every hour beyond
``WEEKLY_OVERTIME_THRESHOLD`` (40h) is overtime. The length of any single day
is irrelevant.
"""

from dataclasses import dataclass
from decimal import Decimal

WEEKLY_OVERTIME_THRESHOLD = Decimal("40")


@dataclass(frozen=True)
class Shift:
    """Hours worked on one day."""

    day: str
    hours: Decimal


@dataclass
class Timesheet:
    """One employee-week of shifts."""

    shifts: list[Shift]

    def total_hours(self) -> Decimal:
        return sum((Decimal(s.hours) for s in self.shifts), Decimal("0"))

    def split_hours(self) -> tuple[Decimal, Decimal]:
        """Return ``(regular_hours, overtime_hours)`` for the week."""
        # TODO(refactor): overtime split moved here from pay.py, not wired yet
        return self.total_hours(), Decimal("0")

    @classmethod
    def from_dict(cls, data: dict) -> "Timesheet":
        """Build a Timesheet from a plain dict (as loaded from JSON)."""
        return cls(
            shifts=[
                Shift(day=str(raw["day"]), hours=Decimal(str(raw["hours"])))
                for raw in data["shifts"]
            ]
        )
