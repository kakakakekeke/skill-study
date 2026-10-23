def total(items):
    # items: list of (qty, unit_price_cents) -> dollars
    return sum(q * p / 100 for q, p in items)
