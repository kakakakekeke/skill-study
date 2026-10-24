from decimal import ROUND_HALF_UP, Decimal


def round_won(value) -> int:
    """원 단위 사사오입. 모든 금액 계산은 마지막에 이 함수를 거친다."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
