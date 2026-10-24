from store.coupons import apply_coupon
from store.customers import tier_discount
from store.pricing import subtotal
from store.shipping import shipping_fee
from store.tax import vat


def build_receipt(lines, region, weight_kg, tier="basic", coupon=None):
    items = subtotal(lines)
    after_tier = items - tier_discount(items, tier)
    after_coupon = apply_coupon(after_tier, coupon) if coupon else after_tier
    ship = shipping_fee(weight_kg, region, items)
    tax = vat(after_coupon)
    return {
        "items": items,
        "discounted": after_coupon,
        "vat": tax,
        "shipping": ship,
        "total": after_coupon + tax + ship,
    }
