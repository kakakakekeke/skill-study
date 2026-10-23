# payroll

payroll — small weekly payroll library (timesheet -> pay stub).

Tests: `python3 -m pytest`

CLI: `python3 -m payroll.cli <timesheet.json>`

## Rules

- **Money.** All amounts are `Decimal`. Every amount is rounded **half-up** to
  whole cents (`0.025 -> 0.03`, `0.035 -> 0.04`, `1.004 -> 1.00`). Banker's
  rounding is never used.
- **Overtime.** Overtime is **weekly**: hours beyond 40 in the week are paid at
  1.5x. Daily hours do not matter (a 10h day in a 38h week has no overtime).
- **Withholding.** A flat-rate table by weekly gross. Bracket upper bounds are
  **inclusive**: a gross of exactly `500.00` is taxed at the 10% rate, not 20%.

  | weekly gross        | rate |
  |---------------------|------|
  | 0.00 – 500.00       | 10%  |
  | 500.01 – 1500.00    | 20%  |
  | above 1500.00       | 30%  |

## API

`payroll.pay.compute_pay(timesheet, rate=Decimal("20.00"))` returns a `PayStub`
with `regular_hours`, `overtime_hours`, `regular_pay`, `overtime_pay`, `gross`,
`withholding`, `net`.
