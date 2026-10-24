import datetime

from store.reports import daily_line


def test_daily_line():
    line = daily_line(datetime.date(2026, 3, 9), [{"total": 12000}, {"total": 3500}])
    assert line == "2026-03-09 주문 2건 합계 15,500원"
