from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from .database import connect, data_dir

POSITION_TYPES = frozenset({"w2", "contractor_1099", "lease_on", "owner_op"})
PAY_METHODS = frozenset(
    {"per_mile", "hourly", "percentage", "salary", "load_pay", "mixed"}
)
SCENARIO_TYPES = frozenset({"conservative", "base", "best"})
RISK_LEVELS = frozenset({"low", "medium", "high"})

ESTIMATE_DISCLAIMER = (
    "All figures are estimates for comparison only. Verify every number with the carrier. "
    "This is not tax, legal, or financial advice."
)

SCENARIO_FIELDS = [
    "weekly_miles",
    "weekly_hours",
    "loaded_miles",
    "empty_miles",
    "gross_pay_weekly",
    "accessorials_weekly",
    "bonuses_weekly",
    "benefits_value_weekly",
    "payroll_tax_weekly",
    "income_tax_reserve_weekly",
    "self_employment_tax_weekly",
    "health_insurance_weekly",
    "retirement_weekly",
    "truck_payment_weekly",
    "trailer_rental_weekly",
    "maintenance_escrow_weekly",
    "performance_escrow_weekly",
    "insurance_weekly",
    "fuel_weekly",
    "tolls_weekly",
    "admin_fees_weekly",
    "carrier_percentage",
    "other_deductions_weekly",
    "downtime_reserve_weekly",
]


@dataclass
class CalculationResult:
    weekly_gross: float
    weekly_deductions: float
    weekly_net: float
    monthly_net: float
    annual_net: float
    net_per_dispatched_mile: float
    net_per_driven_mile: float
    net_per_hour: float
    risk_score: int
    risk_level: str
    calculation_notes: str


def _float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _risk_level(score: int) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _parse_flags(raw: str | list[dict] | None) -> list[dict]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _risk_score_from_flags(flags: list[dict]) -> int:
    score = 0
    for flag in flags:
        level = str(flag.get("level", "")).lower()
        if level == "red":
            score += 3
        elif level == "yellow":
            score += 1
        elif level == "green":
            score -= 1
    return max(score, 0)


def calculate_plan_result(
    *,
    position_type: str,
    scenario: dict[str, Any],
    flags: list[dict] | None = None,
) -> CalculationResult:
    position = position_type.strip().lower()
    if position not in POSITION_TYPES:
        raise ValueError(f"Invalid position_type: {position_type}")

    weekly_miles = _float(scenario.get("weekly_miles"))
    weekly_hours = _float(scenario.get("weekly_hours"))
    loaded_miles = _float(scenario.get("loaded_miles")) or weekly_miles
    empty_miles = _float(scenario.get("empty_miles"))

    gross_pay = _float(scenario.get("gross_pay_weekly"))
    accessorials = _float(scenario.get("accessorials_weekly"))
    bonuses = _float(scenario.get("bonuses_weekly"))
    benefits_value = _float(scenario.get("benefits_value_weekly"))

    payroll_tax = _float(scenario.get("payroll_tax_weekly"))
    income_tax = _float(scenario.get("income_tax_reserve_weekly"))
    se_tax = _float(scenario.get("self_employment_tax_weekly"))
    health = _float(scenario.get("health_insurance_weekly"))
    retirement = _float(scenario.get("retirement_weekly"))

    truck_payment = _float(scenario.get("truck_payment_weekly"))
    trailer_rental = _float(scenario.get("trailer_rental_weekly"))
    maintenance_escrow = _float(scenario.get("maintenance_escrow_weekly"))
    performance_escrow = _float(scenario.get("performance_escrow_weekly"))
    insurance = _float(scenario.get("insurance_weekly"))
    fuel = _float(scenario.get("fuel_weekly"))
    tolls = _float(scenario.get("tolls_weekly"))
    admin_fees = _float(scenario.get("admin_fees_weekly"))
    carrier_pct = _float(scenario.get("carrier_percentage"))
    other_deductions = _float(scenario.get("other_deductions_weekly"))
    downtime_reserve = _float(scenario.get("downtime_reserve_weekly"))

    notes: list[str] = []

    if position == "w2":
        weekly_gross = gross_pay + accessorials + bonuses + benefits_value
        weekly_deductions = (
            payroll_tax
            + income_tax
            + health
            + retirement
            + other_deductions
        )
        notes.append("W-2: benefits counted as estimated total value, not cash in pocket.")
        notes.append("Employer-side payroll costs are not deducted from driver net here.")
    elif position == "contractor_1099":
        weekly_gross = gross_pay + accessorials + bonuses
        weekly_deductions = (
            se_tax
            + income_tax
            + truck_payment
            + trailer_rental
            + maintenance_escrow
            + insurance
            + fuel
            + tolls
            + admin_fees
            + downtime_reserve
            + other_deductions
        )
        notes.append("1099: self-employment and income tax reserves reduce net sharply.")
        notes.append("No employer benefits assumed unless you enter them separately.")
    elif position in {"lease_on", "owner_op"}:
        linehaul = gross_pay
        weekly_gross = linehaul + accessorials + bonuses
        carrier_take = (linehaul + accessorials) * (carrier_pct / 100.0)
        weekly_deductions = (
            carrier_take
            + truck_payment
            + trailer_rental
            + maintenance_escrow
            + performance_escrow
            + insurance
            + fuel
            + tolls
            + admin_fees
            + se_tax
            + income_tax
            + downtime_reserve
            + other_deductions
        )
        label = "Lease-on" if position == "lease_on" else "Owner-op"
        notes.append(f"{label}: carrier percentage and escrows can erase headline gross.")
    else:
        raise ValueError(f"Unsupported position_type: {position_type}")

    weekly_net = round(weekly_gross - weekly_deductions, 2)
    monthly_net = round(weekly_net * 52 / 12, 2)
    annual_net = round(weekly_net * 52, 2)

    dispatched_miles = loaded_miles if loaded_miles > 0 else weekly_miles
    driven_miles = weekly_miles if weekly_miles > 0 else loaded_miles + empty_miles

    net_per_dispatched = round(weekly_net / dispatched_miles, 4) if dispatched_miles > 0 else 0.0
    net_per_driven = round(weekly_net / driven_miles, 4) if driven_miles > 0 else 0.0
    net_per_hour = round(weekly_net / weekly_hours, 2) if weekly_hours > 0 else 0.0

    risk_score = _risk_score_from_flags(flags or [])
    if position in {"lease_on", "owner_op"} and performance_escrow + maintenance_escrow > 0:
        risk_score += 2
    if position == "contractor_1099" and se_tax <= 0:
        risk_score += 2
        notes.append("Warning: no self-employment tax reserve entered for 1099 plan.")

    return CalculationResult(
        weekly_gross=round(weekly_gross, 2),
        weekly_deductions=round(weekly_deductions, 2),
        weekly_net=weekly_net,
        monthly_net=monthly_net,
        annual_net=annual_net,
        net_per_dispatched_mile=net_per_dispatched,
        net_per_driven_mile=net_per_driven,
        net_per_hour=net_per_hour,
        risk_score=risk_score,
        risk_level=_risk_level(risk_score),
        calculation_notes=" ".join(notes),
    )


def _scenario_payload(scenario: dict[str, Any]) -> dict[str, Any]:
    payload = {field: _float(scenario.get(field)) for field in SCENARIO_FIELDS}
    extras = scenario.get("extras_json")
    if isinstance(extras, dict):
        payload["extras_json"] = json.dumps(extras)
    elif isinstance(extras, str):
        payload["extras_json"] = extras
    else:
        payload["extras_json"] = "{}"
    return payload


def create_comp_plan(payload: dict[str, Any]) -> dict:
    company_name = str(payload.get("company_name", "")).strip()
    position_type = str(payload.get("position_type", "")).strip().lower()
    pay_method = str(payload.get("pay_method", "mixed")).strip().lower()

    if not company_name:
        raise ValueError("company_name is required")
    if position_type not in POSITION_TYPES:
        raise ValueError(f"Invalid position_type: {position_type}")
    if pay_method not in PAY_METHODS:
        raise ValueError(f"Invalid pay_method: {pay_method}")

    flags = payload.get("flags") or []
    scenarios = payload.get("scenarios") or [{"scenario_type": "base", **payload.get("base_scenario", {})}]

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO comp_plans (
                company_name, position_type, pay_method, home_time_notes, flags_json, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                position_type,
                pay_method,
                payload.get("home_time_notes"),
                json.dumps(flags),
                payload.get("notes"),
            ),
        )
        plan_id = cursor.lastrowid

        for scenario in scenarios:
            scenario_type = str(scenario.get("scenario_type", "base")).strip().lower()
            if scenario_type not in SCENARIO_TYPES:
                raise ValueError(f"Invalid scenario_type: {scenario_type}")
            fields = _scenario_payload(scenario)
            conn.execute(
                f"""
                INSERT INTO comp_plan_scenarios (
                    plan_id, scenario_type, {", ".join(SCENARIO_FIELDS)}, extras_json
                ) VALUES (
                    ?, ?, {", ".join("?" for _ in SCENARIO_FIELDS)}, ?
                )
                """,
                (plan_id, scenario_type, *[fields[field] for field in SCENARIO_FIELDS], fields["extras_json"]),
            )
            result = calculate_plan_result(
                position_type=position_type,
                scenario=fields,
                flags=flags,
            )
            conn.execute(
                """
                INSERT INTO comp_plan_results (
                    plan_id, scenario_type, weekly_gross, weekly_deductions, weekly_net,
                    monthly_net, annual_net, net_per_dispatched_mile, net_per_driven_mile,
                    net_per_hour, risk_score, risk_level, calculation_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    scenario_type,
                    result.weekly_gross,
                    result.weekly_deductions,
                    result.weekly_net,
                    result.monthly_net,
                    result.annual_net,
                    result.net_per_dispatched_mile,
                    result.net_per_driven_mile,
                    result.net_per_hour,
                    result.risk_score,
                    result.risk_level,
                    result.calculation_notes,
                ),
            )

    return get_comp_plan(plan_id)


def get_comp_plan(plan_id: int) -> dict:
    with connect() as conn:
        plan = conn.execute("SELECT * FROM comp_plans WHERE id = ?", (plan_id,)).fetchone()
        if not plan:
            raise ValueError(f"Comp plan not found: {plan_id}")

        scenarios = conn.execute(
            "SELECT * FROM comp_plan_scenarios WHERE plan_id = ? ORDER BY scenario_type",
            (plan_id,),
        ).fetchall()
        results = conn.execute(
            "SELECT * FROM comp_plan_results WHERE plan_id = ? ORDER BY scenario_type",
            (plan_id,),
        ).fetchall()

    plan_dict = dict(plan)
    plan_dict["flags"] = _parse_flags(plan_dict.pop("flags_json"))
    plan_dict["scenarios"] = [dict(row) for row in scenarios]
    plan_dict["results"] = [dict(row) for row in results]
    return plan_dict


def list_comp_plans() -> list[dict]:
    with connect() as conn:
        plans = conn.execute(
            "SELECT id, company_name, position_type, pay_method, notes, created_at, updated_at FROM comp_plans ORDER BY company_name"
        ).fetchall()
        output = []
        for plan in plans:
            base_result = conn.execute(
                """
                SELECT weekly_net, annual_net, net_per_dispatched_mile, net_per_hour, risk_level
                FROM comp_plan_results
                WHERE plan_id = ? AND scenario_type = 'base'
                """,
                (plan["id"],),
            ).fetchone()
            item = dict(plan)
            item["base_result"] = dict(base_result) if base_result else None
            output.append(item)
    return output


def delete_comp_plan(plan_id: int) -> None:
    with connect() as conn:
        result = conn.execute("DELETE FROM comp_plans WHERE id = ?", (plan_id,))
        if result.rowcount == 0:
            raise ValueError(f"Comp plan not found: {plan_id}")


def compare_comp_plans(
    plan_ids: list[int],
    *,
    scenario_type: str = "base",
) -> list[dict]:
    scenario = scenario_type.strip().lower()
    if scenario not in SCENARIO_TYPES:
        raise ValueError(f"Invalid scenario_type: {scenario_type}")

    rows: list[dict] = []
    for plan_id in plan_ids:
        plan = get_comp_plan(plan_id)
        result = next((r for r in plan["results"] if r["scenario_type"] == scenario), None)
        if not result:
            continue
        rows.append(
            {
                "plan_id": plan["id"],
                "company_name": plan["company_name"],
                "position_type": plan["position_type"],
                "pay_method": plan["pay_method"],
                "weekly_net": result["weekly_net"],
                "monthly_net": result["monthly_net"],
                "annual_net": result["annual_net"],
                "net_per_dispatched_mile": result["net_per_dispatched_mile"],
                "net_per_driven_mile": result["net_per_driven_mile"],
                "net_per_hour": result["net_per_hour"],
                "risk_score": result["risk_score"],
                "risk_level": result["risk_level"],
                "flags": plan["flags"],
                "notes": plan.get("notes"),
                "calculation_notes": result["calculation_notes"],
            }
        )

    rows.sort(key=lambda row: row["weekly_net"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


def export_comp_plans_csv(path: Path | None = None) -> Path:
    export_path = path or (data_dir() / "comp_plans_export.csv")
    plans = list_comp_plans()

    fieldnames = [
        "company_name",
        "position_type",
        "pay_method",
        "scenario_type",
        "weekly_net",
        "monthly_net",
        "annual_net",
        "net_per_dispatched_mile",
        "net_per_hour",
        "risk_level",
        "notes",
    ]

    with export_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in plans:
            plan = get_comp_plan(summary["id"])
            for result in plan["results"]:
                writer.writerow(
                    {
                        "company_name": plan["company_name"],
                        "position_type": plan["position_type"],
                        "pay_method": plan["pay_method"],
                        "scenario_type": result["scenario_type"],
                        "weekly_net": result["weekly_net"],
                        "monthly_net": result["monthly_net"],
                        "annual_net": result["annual_net"],
                        "net_per_dispatched_mile": result["net_per_dispatched_mile"],
                        "net_per_hour": result["net_per_hour"],
                        "risk_level": result["risk_level"],
                        "notes": plan.get("notes") or "",
                    }
                )
    return export_path


def import_comp_plans_csv(source: Path | StringIO) -> dict:
    if isinstance(source, Path):
        handle = source.open(newline="", encoding="utf-8-sig")
        close_handle = True
    else:
        handle = source
        close_handle = False

    imported = 0
    errors: list[str] = []

    try:
        reader = csv.DictReader(handle)
        grouped: dict[str, dict[str, Any]] = {}

        for line_number, row in enumerate(reader, start=2):
            company = (row.get("company_name") or "").strip()
            if not company:
                errors.append(f"Row {line_number}: company_name is required")
                continue

            position_type = (row.get("position_type") or "w2").strip().lower()
            pay_method = (row.get("pay_method") or "mixed").strip().lower()
            key = f"{company}|{position_type}|{pay_method}"

            if key not in grouped:
                grouped[key] = {
                    "company_name": company,
                    "position_type": position_type,
                    "pay_method": pay_method,
                    "notes": row.get("notes"),
                    "scenarios": [],
                }

            scenario_type = (row.get("scenario_type") or "base").strip().lower()
            scenario = {"scenario_type": scenario_type}
            for field in SCENARIO_FIELDS:
                if field in row and row[field] not in (None, ""):
                    scenario[field] = row[field]
            grouped[key]["scenarios"].append(scenario)

        for payload in grouped.values():
            try:
                create_comp_plan(payload)
                imported += 1
            except ValueError as exc:
                errors.append(f"{payload['company_name']}: {exc}")
    finally:
        if close_handle:
            handle.close()

    return {
        "imported": imported,
        "errors": errors,
        "message": f"Imported {imported} compensation plan(s)",
    }