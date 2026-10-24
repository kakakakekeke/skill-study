from decimal import Decimal, ROUND_HALF_UP
import math

CENT = Decimal("0.01")


def line_total(unit_price, qty):
    """한 줄 금액 = 단가 × 수량, 센트 단위 반올림."""
    return (Decimal(str(unit_price)) * qty).quantize(CENT, rounding=ROUND_HALF_UP)


def apply_discount(amount, percent):
    """amount에서 percent% 할인한 금액."""
    amount = Decimal(str(amount))
    off = amount * Decimal(str(percent)) / 100
    return (amount - off).quantize(CENT, rounding=ROUND_HALF_UP)


def order_total(lines, percent=0):
    """lines: [(unit_price, qty), ...]"""
    subtotal = sum((line_total(p, q) for p, q in lines), Decimal("0"))
    return apply_discount(subtotal, percent)


def calcShipping(w, dest):
    # 옛 배송비 계산. 아직 checkout.py가 쓴다
    if dest == "domestic":
        r = 3000
    else:
        r = 12000
    if w > 5:
        r = r + (w - 5) * 500
    return r
