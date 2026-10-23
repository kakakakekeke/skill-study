import sqlite3


def connect(url: str) -> sqlite3.Connection:
    """Open a connection. `url` is a path or ':memory:'."""
    conn = sqlite3.connect(url)
    conn.execute("CREATE TABLE IF NOT EXISTS items (sku TEXT PRIMARY KEY, qty INTEGER NOT NULL)")
    return conn
