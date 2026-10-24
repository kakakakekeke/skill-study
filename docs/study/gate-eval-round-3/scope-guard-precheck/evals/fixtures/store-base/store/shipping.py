from decimal import ROUND_HALF_UP, Decimal

BASE = {"domestic": 3000, "jeju": 6000, "overseas": 15000}


def shipping_fee(weight_kg, region, subtotal):
    if region == "domestic" and subtotal >= 50000:
        return 0
    fee = Decimal(BASE[region])
    if weight_kg > 5:
        fee += Decimal(str(weight_kg - 5)) * Decimal("700")
    return int(fee.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
