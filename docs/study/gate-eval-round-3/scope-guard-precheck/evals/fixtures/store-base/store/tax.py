from decimal import ROUND_HALF_UP, Decimal

VAT_RATE = Decimal("0.1")


def vat(amount):
    """부가세(10%), 원 단위 사사오입."""
    return int((Decimal(amount) * VAT_RATE).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
