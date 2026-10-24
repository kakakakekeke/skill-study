from shop.pricing import order_total, calcShipping
from shop.formatting import format_money


def receipt(lines, weight, dest, percent=0, currency="KRW"):
    total = order_total(lines, percent)
    ship = calcShipping(weight, dest)
    return {
        "items": format_money(total, currency),
        "shipping": format_money(ship, currency),
        "total": format_money(total + ship, currency),
    }
