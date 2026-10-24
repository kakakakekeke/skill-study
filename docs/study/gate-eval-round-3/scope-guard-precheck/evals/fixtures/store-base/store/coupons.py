COUPONS = {
    "WELCOME10": ("percent", 10),
    "SPRING7": ("percent", 7),
    "FLAT3000": ("flat", 3000),
}


def apply_coupon(amount, code):
    """쿠폰 적용 후 금액. 없는 코드는 그대로."""
    if code not in COUPONS:
        return amount
    kind, value = COUPONS[code]
    if kind == "percent":
        return int(amount * (100 - value) / 100)
    return max(0, amount - value)
