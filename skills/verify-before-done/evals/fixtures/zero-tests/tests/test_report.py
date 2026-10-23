from app.inventory import add_stock
from app.report import low_stock


def test_low_stock(conn):
    add_stock(conn, "A1", 2)
    add_stock(conn, "B2", 10)
    add_stock(conn, "C3", 4)
    assert low_stock(conn) == ["A1", "C3"]
