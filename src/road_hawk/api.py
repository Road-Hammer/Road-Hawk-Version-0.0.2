from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .services import (
    TripInput,
    bootstrap,
    dashboard_stats,
    ensure_driver,
    ensure_truck,
    export_trips_csv,
    fuel_efficiency_report,
    list_drivers,
    list_maintenance,
    list_recent_trips,
    list_trucks,
    log_maintenance,
    log_trip,
)

app = FastAPI(title="Road Hawk API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    bootstrap()


class DriverCreate(BaseModel):
    driver_id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class TruckCreate(BaseModel):
    truck_number: str = Field(min_length=1)
    vin: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None


class TripCreate(BaseModel):
    driver_id: str = Field(min_length=1)
    truck_number: str = Field(min_length=1)
    miles_driven: float = Field(gt=0)
    fuel_used: float = Field(gt=0)
    load_weight: float | None = None
    hours_driven: float | None = None
    fuel_price: float | None = None
    location: str | None = None


class MaintenanceCreate(BaseModel):
    truck_number: str = Field(min_length=1)
    service_date: str = Field(min_length=1)
    details: str = Field(min_length=1)
    cost: float | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "road-hawk"}


@app.get("/api/stats")
def stats() -> dict:
    return dashboard_stats()


@app.get("/api/drivers")
def drivers() -> list[dict]:
    return list_drivers()


@app.post("/api/drivers", status_code=201)
def create_driver(payload: DriverCreate) -> dict:
    ensure_driver(payload.driver_id, payload.name)
    return {"driver_id": payload.driver_id, "name": payload.name}


@app.get("/api/trucks")
def trucks() -> list[dict]:
    return list_trucks()


@app.post("/api/trucks", status_code=201)
def create_truck(payload: TruckCreate) -> dict:
    ensure_truck(
        payload.truck_number,
        vin=payload.vin,
        make=payload.make,
        model=payload.model,
        year=payload.year,
    )
    return payload.model_dump()


@app.get("/api/trips")
def trips(limit: Annotated[int, Query(ge=1, le=100)] = 25) -> list[dict]:
    return list_recent_trips(limit=limit)


@app.post("/api/trips", status_code=201)
def create_trip(payload: TripCreate) -> dict:
    try:
        result = log_trip(TripInput(**payload.model_dump()))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {**payload.model_dump(), **result}


@app.get("/api/fuel-report")
def fuel_report(driver_id: str | None = None) -> list[dict]:
    return fuel_efficiency_report(driver_id)


@app.get("/api/maintenance")
def maintenance(limit: Annotated[int, Query(ge=1, le=100)] = 25) -> list[dict]:
    return list_maintenance(limit=limit)


@app.post("/api/maintenance", status_code=201)
def create_maintenance(payload: MaintenanceCreate) -> dict:
    ensure_truck(payload.truck_number)
    record_id = log_maintenance(
        payload.truck_number,
        payload.service_date,
        payload.details,
        payload.cost,
    )
    return {"id": record_id, **payload.model_dump()}


@app.post("/api/export/trips")
def export_trips() -> dict:
    path = export_trips_csv()
    return {"path": str(path), "message": "Trips exported to CSV"}