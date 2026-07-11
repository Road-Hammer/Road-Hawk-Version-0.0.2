import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import auth_services, config, database, services  # noqa: E402
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


def test_default_api_host_is_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROAD_HAWK_API_HOST", raising=False)
    monkeypatch.delenv("ROAD_HAWK_MODE", raising=False)
    assert config.api_host() == "127.0.0.1"
    assert config.is_loopback_host() is True
    assert auth_services.auth_required() is False


def test_non_loopback_bind_forces_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROAD_HAWK_API_HOST", "0.0.0.0")
    monkeypatch.delenv("ROAD_HAWK_AUTH_REQUIRED", raising=False)
    assert config.is_externally_exposed() is True
    assert auth_services.auth_required() is True


def test_server_mode_forces_auth_even_on_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROAD_HAWK_MODE", "server")
    monkeypatch.setenv("ROAD_HAWK_API_HOST", "127.0.0.1")
    monkeypatch.setenv("ROAD_HAWK_AUTH_REQUIRED", "0")
    assert auth_services.auth_required() is True


def test_remote_first_user_api_bootstrap_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ROAD_HAWK_API_HOST", "0.0.0.0")
    monkeypatch.delenv("ROAD_HAWK_ADMIN_USER", raising=False)
    monkeypatch.delenv("ROAD_HAWK_ADMIN_PASSWORD", raising=False)
    database.set_data_root(tmp_path)
    services.bootstrap()

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/auth/bootstrap",
            json={"username": "attacker", "password": "secret123", "role": "admin"},
        )
        assert response.status_code == 400
        assert "Remote first-user bootstrap is disabled" in response.json()["detail"]

    database.set_data_root(None)


def test_auth_required_blocks_stats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ROAD_HAWK_AUTH_REQUIRED", "1")
    monkeypatch.setenv("ROAD_HAWK_ADMIN_USER", "fleet-admin")
    monkeypatch.setenv("ROAD_HAWK_ADMIN_PASSWORD", "road-hawk-test-secret")
    database.set_data_root(tmp_path)
    services.bootstrap()

    with TestClient(app) as test_client:
        blocked = test_client.get("/api/stats")
        assert blocked.status_code == 401

        login = test_client.post(
            "/api/auth/login",
            json={"username": "fleet-admin", "password": "road-hawk-test-secret"},
        )
        assert login.status_code == 200
        token = login.json()["token"]
        allowed = test_client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})
        assert allowed.status_code == 200

    database.set_data_root(None)
    monkeypatch.delenv("ROAD_HAWK_AUTH_REQUIRED", raising=False)
    monkeypatch.delenv("ROAD_HAWK_ADMIN_USER", raising=False)
    monkeypatch.delenv("ROAD_HAWK_ADMIN_PASSWORD", raising=False)


def test_reload_is_local_and_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ROAD_HAWK_RELOAD", raising=False)
    monkeypatch.delenv("ROAD_HAWK_API_HOST", raising=False)
    assert config.api_reload() is False

    monkeypatch.setenv("ROAD_HAWK_RELOAD", "1")
    assert config.api_reload() is True

    monkeypatch.setenv("ROAD_HAWK_API_HOST", "0.0.0.0")
    assert config.api_reload() is False
