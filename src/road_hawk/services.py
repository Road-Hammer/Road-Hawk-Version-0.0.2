from __future__ import annotations

import csv
from dataclasses import dataclass
from io import TextIOWrapper
from pathlib import Path
from typing import BinaryIO, TextIO

from .database import connect, data_dir, init_db

TRIP_CSV_FIELDNAMES = [
    "logged_at",
    "driver_id",
    "truck_number",
    "miles_driven",
    "fuel_used",
    "load_weight",
    "hours_driven",
    "mpg",
    "fuel_cost",
    "avg_speed",
    "location",
]


@dataclass
class TripInput:
    driver_id: str
    truck_number: str
    miles_driven: float
    fuel_used: float
    load_weight: float | None = None
    hours_driven: float | None = None
    fuel_price: float | None = None
    location: str | None = None


def ensure_driver(driver_id: str, name: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO drivers (driver_id, name)
            VALUES (?, ?)
            ON CONFLICT(driver_id) DO UPDATE SET name = excluded.name
            """,
            (driver_id.strip(), name.strip()),
        )


def ensure_truck(
    truck_number: str,
    *,
    vin: str | None = None,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO trucks (truck_number, vin, make, model, year)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(truck_number) DO UPDATE SET
                vin = COALESCE(excluded.vin, trucks.vin),
                make = COALESCE(excluded.make, trucks.make),
                model = COALESCE(excluded.model, trucks.model),
                year = COALESCE(excluded.year, trucks.year)
            """,
            (truck_number.strip(), vin, make, model, year),
        )


def log_trip(trip: TripInput) -> dict:
    ensure_driver(trip.driver_id, trip.driver_id)
    ensure_truck(trip.truck_number)

    mpg = round(trip.miles_driven / trip.fuel_used, 2) if trip.fuel_used > 0 else 0.0
    fuel_cost = (
        round(trip.fuel_used * trip.fuel_price, 2)
        if trip.fuel_price is not None
        else None
    )
    avg_speed = (
        round(trip.miles_driven / trip.hours_driven, 2)
        if trip.hours_driven and trip.hours_driven > 0
        else None
    )

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO trips (
                driver_id, truck_number, miles_driven, fuel_used, load_weight,
                hours_driven, fuel_price, location, mpg, fuel_cost, avg_speed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trip.driver_id.strip(),
                trip.truck_number.strip(),
                trip.miles_driven,
                trip.fuel_used,
                trip.load_weight,
                trip.hours_driven,
                trip.fuel_price,
                trip.location,
                mpg,
                fuel_cost,
                avg_speed,
            ),
        )
        trip_id = cursor.lastrowid

    return {
        "id": trip_id,
        "mpg": mpg,
        "fuel_cost": fuel_cost,
        "avg_speed": avg_speed,
    }


def list_recent_trips(limit: int = 10) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, driver_id, truck_number, miles_driven, fuel_used,
                   mpg, fuel_cost, location, logged_at
            FROM trips
            ORDER BY logged_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def fuel_efficiency_report(driver_id: str | None = None) -> list[dict]:
    query = """
        SELECT driver_id,
               COUNT(*) AS trip_count,
               ROUND(SUM(miles_driven), 2) AS total_miles,
               ROUND(SUM(fuel_used), 2) AS total_fuel,
               ROUND(AVG(mpg), 2) AS avg_mpg
        FROM trips
    """
    params: tuple = ()
    if driver_id:
        query += " WHERE driver_id = ?"
        params = (driver_id.strip(),)
    query += " GROUP BY driver_id ORDER BY avg_mpg DESC"

    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def log_maintenance(
    truck_number: str,
    service_date: str,
    details: str,
    cost: float | None = None,
) -> int:
    ensure_truck(truck_number)
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO maintenance_records (truck_number, service_date, details, cost)
            VALUES (?, ?, ?, ?)
            """,
            (truck_number.strip(), service_date.strip(), details.strip(), cost),
        )
        return cursor.lastrowid


def list_trucks() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT truck_number, vin, make, model, year FROM trucks ORDER BY truck_number"
        ).fetchall()
    return [dict(row) for row in rows]


def list_drivers() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT driver_id, name FROM drivers ORDER BY driver_id"
        ).fetchall()
    return [dict(row) for row in rows]


def list_maintenance(limit: int = 20) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, truck_number, service_date, details, cost, created_at
            FROM maintenance_records
            ORDER BY service_date DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def dashboard_stats() -> dict:
    with connect() as conn:
        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS trip_count,
                ROUND(COALESCE(SUM(miles_driven), 0), 2) AS total_miles,
                ROUND(COALESCE(SUM(fuel_used), 0), 2) AS total_fuel,
                ROUND(COALESCE(AVG(mpg), 0), 2) AS avg_mpg,
                ROUND(COALESCE(SUM(fuel_cost), 0), 2) AS total_fuel_cost
            FROM trips
            """
        ).fetchone()
        driver_count = conn.execute("SELECT COUNT(*) AS count FROM drivers").fetchone()["count"]
        truck_count = conn.execute("SELECT COUNT(*) AS count FROM trucks").fetchone()["count"]
        maintenance_count = conn.execute(
            "SELECT COUNT(*) AS count FROM maintenance_records"
        ).fetchone()["count"]

    return {
        "trip_count": totals["trip_count"],
        "total_miles": totals["total_miles"],
        "total_fuel": totals["total_fuel"],
        "avg_mpg": totals["avg_mpg"],
        "total_fuel_cost": totals["total_fuel_cost"],
        "driver_count": driver_count,
        "truck_count": truck_count,
        "maintenance_count": maintenance_count,
    }


def export_trips_csv(path: Path | None = None) -> Path:
    export_path = path or (data_dir() / "trips_export.csv")
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT logged_at, driver_id, truck_number, miles_driven, fuel_used,
                   load_weight, hours_driven, mpg, fuel_cost, avg_speed, location
            FROM trips
            ORDER BY logged_at DESC
            """
        ).fetchall()

    with export_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRIP_CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in TRIP_CSV_FIELDNAMES})

    return export_path


def _optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    if not cleaned:
        return None
    return float(cleaned)


def _trip_row_from_csv(row: dict[str, str | None]) -> TripInput:
    driver_id = (row.get("driver_id") or "").strip()
    truck_number = (row.get("truck_number") or "").strip()
    miles_raw = (row.get("miles_driven") or "").strip()
    fuel_raw = (row.get("fuel_used") or "").strip()

    if not driver_id:
        raise ValueError("driver_id is required")
    if not truck_number:
        raise ValueError("truck_number is required")
    if not miles_raw:
        raise ValueError("miles_driven is required")
    if not fuel_raw:
        raise ValueError("fuel_used is required")

    miles_driven = float(miles_raw)
    fuel_used = float(fuel_raw)
    if miles_driven <= 0:
        raise ValueError("miles_driven must be greater than 0")
    if fuel_used <= 0:
        raise ValueError("fuel_used must be greater than 0")

    fuel_price = _optional_float(row.get("fuel_price"))
    fuel_cost = _optional_float(row.get("fuel_cost"))
    if fuel_price is None and fuel_cost is not None and fuel_used > 0:
        fuel_price = round(fuel_cost / fuel_used, 4)

    location = (row.get("location") or "").strip() or None

    return TripInput(
        driver_id=driver_id,
        truck_number=truck_number,
        miles_driven=miles_driven,
        fuel_used=fuel_used,
        load_weight=_optional_float(row.get("load_weight")),
        hours_driven=_optional_float(row.get("hours_driven")),
        fuel_price=fuel_price,
        location=location,
    )


def import_trips_csv(
    source: Path | BinaryIO | TextIO,
    *,
    filename: str = "import.csv",
) -> dict:
    if isinstance(source, Path):
        handle: TextIO = source.open(newline="", encoding="utf-8-sig")
        close_handle = True
    elif isinstance(source, TextIO):
        handle = source
        close_handle = False
    else:
        handle = TextIOWrapper(source, encoding="utf-8-sig", newline="")
        close_handle = True

    imported = 0
    skipped = 0
    errors: list[str] = []

    try:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV file is missing a header row")

        normalized_headers = {
            (name or "").strip().lower(): name for name in reader.fieldnames if name
        }
        required_headers = {"driver_id", "truck_number", "miles_driven", "fuel_used"}
        missing_headers = sorted(required_headers - set(normalized_headers))
        if missing_headers:
            joined = ", ".join(missing_headers)
            raise ValueError(f"CSV is missing required columns: {joined}")

        for line_number, raw_row in enumerate(reader, start=2):
            if not any((value or "").strip() for value in raw_row.values()):
                skipped += 1
                continue

            normalized_row = {
                key.strip().lower(): (value.strip() if isinstance(value, str) else value)
                for key, value in raw_row.items()
                if key
            }

            try:
                trip = _trip_row_from_csv(normalized_row)
                result = log_trip(trip)
                logged_at = (normalized_row.get("logged_at") or "").strip()
                if logged_at:
                    with connect() as conn:
                        conn.execute(
                            "UPDATE trips SET logged_at = ? WHERE id = ?",
                            (logged_at, result["id"]),
                        )
                imported += 1
            except (ValueError, TypeError) as exc:
                errors.append(f"Row {line_number}: {exc}")
    finally:
        if close_handle:
            handle.close()

    return {
        "filename": filename,
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "message": f"Imported {imported} trip(s) from {filename}",
    }


def bootstrap() -> None:
    init_db()
    from .auth_services import ensure_bootstrap_admin
    from .chain_services import ensure_chain_profile

    ensure_chain_profile()
    ensure_bootstrap_admin()