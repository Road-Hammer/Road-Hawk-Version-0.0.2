from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_number TEXT NOT NULL UNIQUE,
    vin TEXT,
    make TEXT,
    model TEXT,
    year INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL,
    truck_number TEXT NOT NULL,
    miles_driven REAL NOT NULL,
    fuel_used REAL NOT NULL,
    load_weight REAL,
    hours_driven REAL,
    fuel_price REAL,
    location TEXT,
    mpg REAL NOT NULL,
    fuel_cost REAL,
    avg_speed REAL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    FOREIGN KEY (truck_number) REFERENCES trucks(truck_number)
);

CREATE TABLE IF NOT EXISTS maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    truck_number TEXT NOT NULL,
    service_date TEXT NOT NULL,
    details TEXT NOT NULL,
    cost REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (truck_number) REFERENCES trucks(truck_number)
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type TEXT NOT NULL DEFAULT 'unknown',
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    mime_type TEXT,
    source_type TEXT NOT NULL DEFAULT 'upload',
    extraction_method TEXT NOT NULL DEFAULT 'manual',
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    driver_id TEXT,
    truck_number TEXT,
    load_number TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
    FOREIGN KEY (truck_number) REFERENCES trucks(truck_number)
);

CREATE TABLE IF NOT EXISTS document_extractions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    raw_text TEXT NOT NULL DEFAULT '',
    ocr_confidence REAL,
    parser_version TEXT NOT NULL,
    extraction_notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    extracted_value TEXT,
    corrected_value TEXT,
    confidence REAL,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE (document_id, field_name)
);
"""


_override_root: Path | None = None


def set_data_root(path: Path | None) -> None:
    global _override_root
    _override_root = path


def repo_root() -> Path:
    if _override_root is not None:
        return _override_root
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    path = repo_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def uploads_dir() -> Path:
    path = data_dir() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def db_path() -> Path:
    return data_dir() / "road_hawk.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)