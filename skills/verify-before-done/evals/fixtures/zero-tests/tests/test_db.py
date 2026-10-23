from app.db import connect


def test_connect_creates_items_table():
    c = connect(":memory:")
    names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    assert "items" in names
