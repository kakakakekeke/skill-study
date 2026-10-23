from decimal import ROUND_HALF_UP, Decimal


def apply_discount(price: Decimal, pct: int) -> Decimal:
    """Return price reduced by pct percent (0-100), rounded to cents."""
    discounted = price * (Decimal(100 - pct) / Decimal(100))
    return discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_price(amount: Decimal, currency: str = "USD") -> str:
    symbol = {"USD": "$", "EUR": "EUR", "GBP": "£"}.get(currency, currency + " ")
    return f"{symbol}{amount:.2f}"
