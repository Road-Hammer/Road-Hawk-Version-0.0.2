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

CREATE TABLE IF NOT EXISTS chain_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chained_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'driver',
    api_url TEXT,
    contact TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS app_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'driver',
    display_name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS app_sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES app_users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comp_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    position_type TEXT NOT NULL,
    pay_method TEXT NOT NULL DEFAULT 'mixed',
    home_time_notes TEXT,
    flags_json TEXT NOT NULL DEFAULT '[]',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS comp_plan_scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    scenario_type TEXT NOT NULL,
    weekly_miles REAL NOT NULL DEFAULT 0,
    weekly_hours REAL NOT NULL DEFAULT 0,
    loaded_miles REAL NOT NULL DEFAULT 0,
    empty_miles REAL NOT NULL DEFAULT 0,
    gross_pay_weekly REAL NOT NULL DEFAULT 0,
    accessorials_weekly REAL NOT NULL DEFAULT 0,
    bonuses_weekly REAL NOT NULL DEFAULT 0,
    benefits_value_weekly REAL NOT NULL DEFAULT 0,
    payroll_tax_weekly REAL NOT NULL DEFAULT 0,
    income_tax_reserve_weekly REAL NOT NULL DEFAULT 0,
    self_employment_tax_weekly REAL NOT NULL DEFAULT 0,
    health_insurance_weekly REAL NOT NULL DEFAULT 0,
    retirement_weekly REAL NOT NULL DEFAULT 0,
    truck_payment_weekly REAL NOT NULL DEFAULT 0,
    trailer_rental_weekly REAL NOT NULL DEFAULT 0,
    maintenance_escrow_weekly REAL NOT NULL DEFAULT 0,
    performance_escrow_weekly REAL NOT NULL DEFAULT 0,
    insurance_weekly REAL NOT NULL DEFAULT 0,
    fuel_weekly REAL NOT NULL DEFAULT 0,
    tolls_weekly REAL NOT NULL DEFAULT 0,
    admin_fees_weekly REAL NOT NULL DEFAULT 0,
    carrier_percentage REAL NOT NULL DEFAULT 0,
    other_deductions_weekly REAL NOT NULL DEFAULT 0,
    downtime_reserve_weekly REAL NOT NULL DEFAULT 0,
    extras_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (plan_id) REFERENCES comp_plans(id) ON DELETE CASCADE,
    UNIQUE (plan_id, scenario_type)
);

CREATE TABLE IF NOT EXISTS comp_plan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    scenario_type TEXT NOT NULL,
    weekly_gross REAL NOT NULL DEFAULT 0,
    weekly_deductions REAL NOT NULL DEFAULT 0,
    weekly_net REAL NOT NULL DEFAULT 0,
    monthly_net REAL NOT NULL DEFAULT 0,
    annual_net REAL NOT NULL DEFAULT 0,
    net_per_dispatched_mile REAL NOT NULL DEFAULT 0,
    net_per_driven_mile REAL NOT NULL DEFAULT 0,
    net_per_hour REAL NOT NULL DEFAULT 0,
    risk_score INTEGER NOT NULL DEFAULT 0,
    risk_level TEXT NOT NULL DEFAULT 'low',
    calculation_notes TEXT,
    calculated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (plan_id) REFERENCES comp_plans(id) ON DELETE CASCADE,
    UNIQUE (plan_id, scenario_type)
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