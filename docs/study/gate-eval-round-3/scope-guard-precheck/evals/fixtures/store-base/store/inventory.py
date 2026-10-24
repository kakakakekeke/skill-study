class OutOfStock(Exception):
    pass


class Inventory:
    def __init__(self, names):
        self.names = dict(names)  # sku -> 상품명
        self.stock = {sku: 0 for sku in self.names}

    def add(self, sku, n):
        self.stock[sku] = self.stock.get(sku, 0) + n

    def take(self, sku, n):
        have = self.stock.get(sku, 0)
        if have < n:
            raise OutOfStock(f"재고 부족: {sku} (요청 {n}, 재고 {have})")
        self.stock[sku] = have - n
