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
        link["label"] == "X" and link["url"] == "https://x.com/1stRoadhammer"
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