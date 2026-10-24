from store.money import round_won


def subtotal(lines):
    """lines: [(unit_price, qty), ...] → 원 단위 소계."""
    return round_won(sum(price * qty for price, qty in lines))
