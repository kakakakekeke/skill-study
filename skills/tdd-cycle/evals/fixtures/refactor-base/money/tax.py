from decimal import ROUND_HALF_UP, Decimal


def apply_tax(amount: float, rate: float = 0.1) -> float:
    gross = Decimal(str(amount)) * (Decimal("1") + Decimal(str(rate)))
    q = Decimal("1").scaleb(-2)
    value = gross.quantize(q, rounding=ROUND_HALF_UP)
    return float(value)
