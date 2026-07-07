import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import database, services  # noqa: E402
from road_hawk.api import app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    with TestClient(app) as test_client:
        yield test_client
    database.set_data_root(None)


def test_api_health_smoke(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "road-hawk"
    assert "copyright" in payload
    assert "trademark_footer" in payload
    assert "Road Hawk™" in payload["trademark_footer"]
    assert "copyright_trademark_notice_legal" in payload
    assert "No public license is currently granted" in payload["copyright_trademark_notice_legal"]
    assert "privacy_footer" in payload
    assert "STWL does not sell" in payload["privacy_footer"]
    assert "contact" in payload
    assert payload["contact"]["location"] == "Montrose, PA — USA"
    assert payload["contact"]["email"] == "office@thatdambbs.com"
    assert payload["contact"]["phone"] == "570-442-0273"
    assert "Monday to Friday" in payload["contact"]["hours"]
    assert any(
        link["label"] == "YouTube" and link["display"] == "YouTube"
        for link in payload["contact"]["links"]
    )
    assert any(
        link["label"] == "X" and link["display"] == "X" and link["url"] == "https://x.com/1stRoadhammer"
        for link in payload["contact"]["links"]
    )
    assert any(
        link["label"] == "YouTube" and "youtube.com" in link["url"]
        for link in payload["contact"]["links"]
    )
    assert any(
        link["label"] == "GitHub" and link["url"] == "https://github.com/Road-Hammer"
        for link in payload["contact"]["links"]
    )
    assert "version" in payload
    assert payload["version"]
    assert "auth_required" in payload
    assert "connection_modes" in payload


def test_api_export_trips_download(client: TestClient) -> None:
    client.post(
        "/api/trips",
        json={
            "driver_id": "RH-001",
            "truck_number": "T-101",
            "miles_driven": 120,
            "fuel_used": 15,
            "location": "I-81",
        },
    )

    response = client.post("/api/export/trips")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "trips_export.csv" in response.headers.get("content-disposition", "")
    assert "RH-001" in response.text
    assert "I-81" in response.text


def test_api_import_trips_upload(client: TestClient) -> None:
    export_response = client.post(
        "/api/trips",
        json={
            "driver_id": "RH-002",
            "truck_number": "T-202",
            "miles_driven": 200,
            "fuel_used": 25,
            "location": "US-6",
        },
    )
    assert export_response.status_code == 201

    csv_response = client.post("/api/export/trips")
    csv_bytes = csv_response.content

    with database.connect() as conn:
        conn.execute("DELETE FROM trips")

    import_response = client.post(
        "/api/import/trips",
        files={"file": ("trips_export.csv", csv_bytes, "text/csv")},
    )
    assert import_response.status_code == 200
    payload = import_response.json()
    assert payload["imported"] == 1
    assert payload["errors"] == []

    trips_response = client.get("/api/trips")
    trips = trips_response.json()
    assert len(trips) == 1
    assert trips[0]["driver_id"] == "RH-002"
    assert trips[0]["location"] == "US-6"