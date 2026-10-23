from app.inventory import add_stock, stock_of


def test_add_stock_accumulates(conn):
    assert add_stock(conn, "A1", 3) == 3
    assert add_stock(conn, "A1", 2) == 5
    assert stock_of(conn, "A1") == 5


def test_stock_of_missing(conn):
    assert stock_of(conn, "ZZ") == 0
