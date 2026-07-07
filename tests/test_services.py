import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import database, services  # noqa: E402


def run_smoke_test() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        tmp_path = Path(tmp)
        database.set_data_root(tmp_path)
        services.bootstrap()

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

        database.set_data_root(None)

    print("All smoke tests passed.")


if __name__ == "__main__":
    run_smoke_test()