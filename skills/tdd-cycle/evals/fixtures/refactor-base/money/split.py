from decimal import ROUND_HALF_UP, Decimal


def split_bill(total: float, n: int) -> list[float]:
    if n <= 0:
        raise ValueError("n must be positive")
    q = Decimal("1").scaleb(-2)
    share = (Decimal(str(total)) / n).quantize(q, rounding=ROUND_HALF_UP)
    shares = [share] * n
    remainder = Decimal(str(total)).quantize(q, rounding=ROUND_HALF_UP) - share * n
    shares[0] = share + remainder
    return [float(s) for s in shares]
