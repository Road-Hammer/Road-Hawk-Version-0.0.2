from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .branding import (
    BRAND,
    BRAND_ASSETS_SOURCE,
    COMPANY_LEGAL,
    COMPANY_SHORT,
    COPYRIGHT_NOTICE,
    PRIVACY_FOOTER_SHORT,
    PRIVACY_NOTICE_ROAD_HAWK_TITLE,
    PRODUCT,
    TAGLINE,
)
from .config import api_url, apply_runtime_config, cors_origins, deploy_mode
from .document_services import (
    export_documents_csv,
    get_document,
    get_document_file_path,
    ingest_document,
    list_documents,
    reject_document,
    reprocess_document,
    verify_document,
)
from .document_types import DOCUMENT_TYPES, SOURCE_TYPES, VERIFICATION_STATUSES
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

app = FastAPI(
    title=f"{PRODUCT} API",
    description=f"{PRODUCT} by {BRAND} — {COMPANY_LEGAL}. {TAGLINE}",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    apply_runtime_config()
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


class DocumentVerify(BaseModel):
    corrected_fields: dict[str, str] = Field(default_factory=dict)
    document_type: str | None = None


class DocumentReject(BaseModel):
    reason: str | None = None
    rejected: bool = False


class DocumentReprocess(BaseModel):
    document_type_hint: str | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "road-hawk",
        "product": PRODUCT,
        "brand": BRAND,
        "company": COMPANY_LEGAL,
        "company_short": COMPANY_SHORT,
        "copyright": COPYRIGHT_NOTICE,
        "privacy_notice": PRIVACY_NOTICE_ROAD_HAWK_TITLE,
        "privacy_footer": PRIVACY_FOOTER_SHORT,
        "brand_assets_source": BRAND_ASSETS_SOURCE,
        "mode": deploy_mode(),
        "api_url": api_url(),
    }


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


@app.post("/api/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form(default="upload"),
    driver_id: str | None = Form(default=None),
    truck_number: str | None = Form(default=None),
    load_number: str | None = Form(default=None),
    document_type_hint: str | None = Form(default=None),
) -> dict:
    if source_type not in SOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid source_type: {source_type}")
    if document_type_hint and document_type_hint not in DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid document_type_hint: {document_type_hint}")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        return ingest_document(
            file.file,
            original_filename=file.filename,
            mime_type=file.content_type,
            source_type=source_type,
            driver_id=driver_id,
            truck_number=truck_number,
            load_number=load_number,
            document_type_hint=document_type_hint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/documents")
def documents(
    driver_id: str | None = None,
    verification_status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict]:
    if verification_status and verification_status not in VERIFICATION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid verification_status: {verification_status}")
    return list_documents(
        driver_id=driver_id,
        verification_status=verification_status,
        limit=limit,
    )


@app.get("/api/documents/{document_id}")
def document_detail(document_id: int) -> dict:
    try:
        return get_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/documents/{document_id}/file")
def document_file(document_id: int) -> FileResponse:
    try:
        path = get_document_file_path(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, filename=path.name)


@app.post("/api/documents/{document_id}/verify")
def verify_document_record(document_id: int, payload: DocumentVerify) -> dict:
    try:
        return verify_document(
            document_id,
            corrected_fields=payload.corrected_fields,
            document_type=payload.document_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/documents/{document_id}/reject")
def reject_document_record(document_id: int, payload: DocumentReject) -> dict:
    try:
        return reject_document(
            document_id,
            reason=payload.reason,
            status="rejected" if payload.rejected else "needs_review",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/documents/{document_id}/reprocess")
def reprocess_document_record(document_id: int, payload: DocumentReprocess) -> dict:
    try:
        return reprocess_document(
            document_id,
            document_type_hint=payload.document_type_hint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/export/documents")
def export_documents() -> dict:
    path = export_documents_csv()
    return {"path": str(path), "message": "Documents exported to CSV"}