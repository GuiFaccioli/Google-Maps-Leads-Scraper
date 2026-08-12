from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    rating REAL,
    review_count INTEGER,
    price_range TEXT,
    category TEXT,
    source_query TEXT,
    source_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, address, phone)
);

CREATE INDEX IF NOT EXISTS idx_leads_name ON leads(name);
CREATE INDEX IF NOT EXISTS idx_leads_category ON leads(category);
CREATE INDEX IF NOT EXISTS idx_leads_source_query ON leads(source_query);
"""


def ensure_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.executescript(SCHEMA_SQL)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(leads)")}
        if "rating" not in columns:
            connection.execute("ALTER TABLE leads ADD COLUMN rating REAL")
        if "review_count" not in columns:
            connection.execute("ALTER TABLE leads ADD COLUMN review_count INTEGER")
        if "price_range" not in columns:
            connection.execute("ALTER TABLE leads ADD COLUMN price_range TEXT")


def open_connection(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection
