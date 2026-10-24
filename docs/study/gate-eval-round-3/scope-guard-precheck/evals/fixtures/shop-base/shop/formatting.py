import os, sys
from decimal import Decimal


def format_money(amount, currency="KRW"):
    amount = Decimal(str(amount))
    if currency == "KRW":
        return f"₩{int(amount):,}"
    if currency == "USD":
        return f"${amount:,.2f}"
    raise ValueError(f"unsupported currency: {currency}")
