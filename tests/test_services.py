import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import database, services  # noqa: E402


@pytest.fixture
def isolated_data_root(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    yield tmp_path
    database.set_data_root(None)


def test_smoke_trip_logging_and_export(isolated_data_root: Path) -> None:
    services.ensure_driver("RH-001", "Road Hammer")
    services.ensure_truck("T-101", make="Freightliner", model="Cascadia", year=2019)

    result = services.log_trip(
        services.TripInput(
            driver_id="RH-001",
            truck_number="T-101",
            miles_driven=450,
            fuel_used=60,
            fuel_price=3.85,
            hours_driven=8,
            location="I-80, PA",
        )
    )

    assert result["mpg"] == 7.5
    assert result["fuel_cost"] == 231.0

    report = services.fuel_efficiency_report("RH-001")
    assert len(report) == 1
    assert report[0]["avg_mpg"] == 7.5

    export_path = services.export_trips_csv()
    assert export_path.exists()
    assert "RH-001" in export_path.read_text(encoding="utf-8")
    assert export_path.parent == isolated_data_root / "data"


def test_import_trips_csv_round_trip(isolated_data_root: Path) -> None:
    services.ensure_driver("RH-001", "Road Hammer")
    services.ensure_truck("T-101")
    services.log_trip(
        services.TripInput(
            driver_id="RH-001",
            truck_number="T-101",
            miles_driven=100,
            fuel_used=10,
            location="PA Turnpike",
        )
    )

    export_path = services.export_trips_csv()

    with database.connect() as conn:
        conn.execute("DELETE FROM trips")

    result = services.import_trips_csv(export_path)
    assert result["imported"] == 1
    assert result["errors"] == []

    trips = services.list_recent_trips(limit=10)
    assert len(trips) == 1
    assert trips[0]["driver_id"] == "RH-001"
    assert trips[0]["location"] == "PA Turnpike"


def test_import_trips_csv_reports_row_errors(isolated_data_root: Path) -> None:
    csv_path = isolated_data_root / "bad_import.csv"
    csv_path.write_text(
        "driver_id,truck_number,miles_driven,fuel_used\n"
        "RH-001,T-101,100,10\n"
        "RH-002,,50,5\n",
        encoding="utf-8",
    )

    result = services.import_trips_csv(csv_path)
    assert result["imported"] == 1
    assert len(result["errors"]) == 1
    assert "truck_number is required" in result["errors"][0]