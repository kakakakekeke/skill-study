import sqlite3


def low_stock(conn: sqlite3.Connection, threshold: int = 5) -> list[str]:
    rows = conn.execute("SELECT sku FROM items WHERE qty < ? ORDER BY sku", (threshold,)).fetchall()
    return [r[0] for r in rows]
