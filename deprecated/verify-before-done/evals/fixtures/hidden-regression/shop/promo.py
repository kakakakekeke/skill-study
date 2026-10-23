from decimal import Decimal

from shop.pricing import apply_discount

SEASONAL = {"SPRING10": 10, "SUMMER25": 25}


def promo_price(price: Decimal, code: str) -> Decimal:
    pct = SEASONAL.get(code.upper(), 0)
    return apply_discount(price, pct)
