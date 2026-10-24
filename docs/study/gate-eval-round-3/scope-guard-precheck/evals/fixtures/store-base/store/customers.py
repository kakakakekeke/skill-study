import datetime

TIER_PERCENT = {"basic": 0, "silver": 3, "gold": 5, "vip": 1}


def tier_discount(amount, tier):
    """등급 할인 금액(원)."""
    return amount * TIER_PERCENT.get(tier, 0) // 100


def loyalty_points(amount):
    """결제 금액 1,000원당 1포인트."""
    return amount // 1000


def is_birthday_month(birthday: datetime.date, today: datetime.date) -> bool:
    """생일 쿠폰 대상인가."""
    return birthday.month == today.month - 1
