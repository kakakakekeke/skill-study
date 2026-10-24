# TODO: 이 모듈은 dict 대신 dataclass로 바꾸기
stock = {}


def add(sku, n):
    stock[sku] = stock.get(sku, 0) + n


def take(sku, n):
    if stock.get(sku, 0) < n:
        raise ValueError("not enough stock")
    stock[sku] -= n
