import sqlite3


def add_stock(conn: sqlite3.Connection, sku: str, qty: int) -> int:
    row = conn.execute("SELECT qty FROM items WHERE sku = ?", (sku,)).fetchone()
    new_qty = (row[0] if row else 0) + qty
    conn.execute("INSERT OR REPLACE INTO items (sku, qty) VALUES (?, ?)", (sku, new_qty))
    conn.commit()
    return new_qty


def stock_of(conn: sqlite3.Connection, sku: str) -> int:
    row = conn.execute("SELECT qty FROM items WHERE sku = ?", (sku,)).fetchone()
    return row[0] if row else 0
