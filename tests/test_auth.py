import os
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


def test_connection_endpoint(client: TestClient) -> None:
    response = client.get("/api/connection")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] in {"standalone", "server", "client"}
    assert "standalone" in payload["connection_modes"]
    assert "auth_required" in payload


def test_bootstrap_and_login(client: TestClient) -> None:
    bootstrap = client.post(
        "/api/auth/bootstrap",
        json={
            "username": "admin",
            "password": "road-hawk-test",
            "display_name": "Fleet Admin",
            "role": "admin",
        },
    )
    assert bootstrap.status_code == 201
    token = bootstrap.json()["token"]

    status = client.get("/api/auth/status", headers={"Authorization": f"Bearer {token}"})
    assert status.status_code == 200
    assert status.json()["authenticated"] is True
    assert status.json()["user"]["username"] == "admin"

    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "road-hawk-test"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "admin"


def test_auth_required_blocks_stats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ROAD_HAWK_AUTH_REQUIRED", "1")
    monkeypatch.delenv("ROAD_HAWK_ADMIN_USER", raising=False)
    monkeypatch.delenv("ROAD_HAWK_ADMIN_PASSWORD", raising=False)
    database.set_data_root(tmp_path)
    services.bootstrap()

    with TestClient(app) as test_client:
        bootstrap = test_client.post(
            "/api/auth/bootstrap",
            json={"username": "driver1", "password": "secret123", "role": "driver"},
        )
        assert bootstrap.status_code == 201
        blocked = test_client.get("/api/stats")
        assert blocked.status_code == 401

        login = test_client.post(
            "/api/auth/login",
            json={"username": "driver1", "password": "secret123"},
        )
        assert login.status_code == 200
        token = login.json()["token"]
        allowed = test_client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})
        assert allowed.status_code == 200

    database.set_data_root(None)
    monkeypatch.delenv("ROAD_HAWK_AUTH_REQUIRED", raising=False)