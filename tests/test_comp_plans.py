import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import comp_services, database, services  # noqa: E402
from road_hawk.api import app  # noqa: E402


@pytest.fixture
def client(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    with TestClient(app) as test_client:
        yield test_client
    database.set_data_root(None)


def test_w2_net_is_lower_than_gross() -> None:
    result = comp_services.calculate_plan_result(
        position_type="w2",
        scenario={
            "weekly_miles": 2500,
            "weekly_hours": 60,
            "gross_pay_weekly": 1800,
            "accessorials_weekly": 150,
            "benefits_value_weekly": 120,
            "payroll_tax_weekly": 140,
            "income_tax_reserve_weekly": 260,
            "health_insurance_weekly": 80,
        },
        flags=[{"level": "green", "message": "clear pay formula"}],
    )
    assert result.weekly_net < 1800 + 150 + 120
    assert result.annual_net == round(result.weekly_net * 52, 2)
    assert result.net_per_dispatched_mile > 0


def test_lease_on_flags_increase_risk() -> None:
    result = comp_services.calculate_plan_result(
        position_type="lease_on",
        scenario={
            "weekly_miles": 2800,
            "gross_pay_weekly": 5200,
            "carrier_percentage": 18,
            "maintenance_escrow_weekly": 250,
            "performance_escrow_weekly": 200,
            "fuel_weekly": 1100,
            "income_tax_reserve_weekly": 300,
        },
        flags=[{"level": "red", "message": "excessive escrow"}],
    )
    assert result.risk_level in {"medium", "high"}
    assert result.weekly_net < 5200


def test_compare_ranks_by_weekly_net(client: TestClient) -> None:
    w2 = client.post(
        "/api/comp-plans",
        json={
            "company_name": "Company B",
            "position_type": "w2",
            "pay_method": "hourly",
            "scenarios": [
                {
                    "scenario_type": "base",
                    "weekly_miles": 2000,
                    "weekly_hours": 50,
                    "gross_pay_weekly": 1400,
                    "income_tax_reserve_weekly": 180,
                    "benefits_value_weekly": 100,
                }
            ],
        },
    ).json()
    lease = client.post(
        "/api/comp-plans",
        json={
            "company_name": "Company D",
            "position_type": "lease_on",
            "pay_method": "percentage",
            "flags": [{"level": "red", "message": "excessive escrow"}],
            "scenarios": [
                {
                    "scenario_type": "base",
                    "weekly_miles": 2800,
                    "gross_pay_weekly": 5000,
                    "carrier_percentage": 20,
                    "maintenance_escrow_weekly": 300,
                    "fuel_weekly": 1200,
                    "income_tax_reserve_weekly": 350,
                }
            ],
        },
    ).json()

    response = client.get(
        f"/api/comp-plans/compare/ranked?ids={w2['id']},{lease['id']}&scenario=base"
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["rank"] == 1
    assert "disclaimer" in payload
    assert payload["results"][0]["weekly_net"] >= payload["results"][1]["weekly_net"]


def test_export_and_meta(client: TestClient) -> None:
    client.post(
        "/api/comp-plans",
        json={
            "company_name": "Export Test Co",
            "position_type": "contractor_1099",
            "pay_method": "per_mile",
            "scenarios": [{"scenario_type": "base", "gross_pay_weekly": 2200, "weekly_miles": 2600}],
        },
    )
    meta = client.get("/api/comp-plans/meta")
    assert meta.status_code == 200
    assert "w2" in meta.json()["position_types"]

    export = client.post("/api/comp-plans/export")
    assert export.status_code == 200
    assert "text/csv" in export.headers["content-type"]
    assert "Export Test Co" in export.text