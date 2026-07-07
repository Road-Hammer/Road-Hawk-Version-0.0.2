import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import chain_services, database, services  # noqa: E402
from road_hawk.api import app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    with TestClient(app) as test_client:
        yield test_client
    database.set_data_root(None)


def test_chain_profile_created_on_bootstrap(client: TestClient) -> None:
    response = client.get("/api/chain/profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_key"].startswith("RH-")
    assert payload["display_name"]
    assert "driver" in payload["roles"]
    assert "broker" in payload["roles"]


def test_add_and_list_chained_users(client: TestClient) -> None:
    profile = client.get("/api/chain/profile").json()
    response = client.post(
        "/api/chain/users",
        json={
            "user_key": "RH-ABCDEF01",
            "display_name": "Dispatch Desk",
            "role": "dispatcher",
            "api_url": "http://192.168.1.20:8000",
            "contact": "dispatch@example.com",
            "status": "active",
            "notes": "Night shift",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["display_name"] == "Dispatch Desk"
    assert created["role"] == "dispatcher"

    users = client.get("/api/chain/users").json()
    assert len(users) == 1
    assert users[0]["user_key"] == "RH-ABCDEF01"

    duplicate = client.post(
        "/api/chain/users",
        json={
            "user_key": "RH-ABCDEF01",
            "display_name": "Duplicate",
            "role": "broker",
        },
    )
    assert duplicate.status_code == 400

    self_chain = client.post(
        "/api/chain/users",
        json={
            "user_key": profile["user_key"],
            "display_name": "Self",
            "role": "driver",
        },
    )
    assert self_chain.status_code == 400


def test_update_and_remove_chained_user(client: TestClient) -> None:
    created = client.post(
        "/api/chain/users",
        json={
            "user_key": "RH-BROKER99",
            "display_name": "Broker One",
            "role": "broker",
            "status": "pending",
        },
    ).json()

    updated = client.patch(
        f"/api/chain/users/{created['id']}",
        json={"status": "active", "notes": "Approved"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "active"
    assert updated.json()["notes"] == "Approved"

    deleted = client.delete(f"/api/chain/users/{created['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/chain/users").json() == []


def test_chain_services_validation(tmp_path: Path) -> None:
    database.set_data_root(tmp_path)
    services.bootstrap()
    profile = chain_services.get_chain_profile()
    with pytest.raises(ValueError, match="own user key"):
        chain_services.add_chained_user(
            user_key=profile["user_key"],
            display_name="Self",
        )
    database.set_data_root(None)