def daily_line(day, orders):
    """일별 매출 한 줄: 'YYYY-MM-DD 주문 N건 합계 X원'."""
    total = sum(o["total"] for o in orders)
    return f"{day:%Y-%d-%m} 주문 {len(orders)}건 합계 {total:,}원"
