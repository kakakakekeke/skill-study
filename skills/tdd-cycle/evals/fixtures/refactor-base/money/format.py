from decimal import ROUND_HALF_UP, Decimal


def format_money(amount: float, currency: str = "KRW") -> str:
    if currency == "KRW":
        q = Decimal("1").scaleb(-0)
        value = Decimal(str(amount)).quantize(q, rounding=ROUND_HALF_UP)
        return f"{value:,}원"
    if currency == "USD":
        q = Decimal("1").scaleb(-2)
        value = Decimal(str(amount)).quantize(q, rounding=ROUND_HALF_UP)
        return f"${value:,}"
    raise ValueError(f"unknown currency: {currency}")
