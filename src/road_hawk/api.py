from __future__ import annotations

from typing import Annotated, Any

from fastapi import FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.requests import Request

from .auth_services import (
    APP_ROLES,
    auth_required,
    auth_status,
    authenticate_user,
    create_session,
    create_user,
    get_user_from_token,
    revoke_session,
)
from .branding import (
    BRAND,
    BRAND_ASSETS_SOURCE,
    COMPANY_LEGAL,
    COMPANY_SHORT,
    CONTACT_EMAIL,
    CONTACT_HOURS,
    CONTACT_LINKS,
    CONTACT_LOCATION,
    CONTACT_ORGANIZATIONS,
    CONTACT_PHONE,
    CONTACT_PHONE_URL,
    CONTACT_TIMEZONE,
    CONTACT_TIMEZONE_LABEL,
    CONTACT_WEBSITE,
    COPYRIGHT_NOTICE,
    COPYRIGHT_TRADEMARK_NOTICE,
    COPYRIGHT_TRADEMARK_NOTICE_LEGAL,
    PRIVACY_FOOTER_SHORT,
    PRIVACY_NOTICE_ROAD_HAWK_TITLE,
    PRODUCT,
    TAGLINE,
    TRADEMARK_FOOTER_SHORT,
)
from .config import api_host, api_port, api_url, apply_runtime_config, connection_modes, cors_origins, deploy_mode
from .version import git_revision, package_version
from .comp_services import (
    ESTIMATE_DISCLAIMER,
    PAY_METHODS,
    POSITION_TYPES,
    SCENARIO_TYPES,
    compare_comp_plans,
    create_comp_plan,
    delete_comp_plan,
    export_comp_plans_csv,
    get_comp_plan,
    import_comp_plans_csv,
    list_comp_plans,
)
from .chain_services import (
    CHAIN_ROLES,
    CHAIN_STATUSES,
    add_chained_user,
    get_chain_profile,
    list_chained_users,
    remove_chained_user,
    update_chain_profile,
    update_chained_user,
)
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
    import_trips_csv,
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
    version=package_version(),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_API_PATHS = {
    "/api/health",
    "/api/connection",
    "/api/auth/login",
    "/api/auth/status",
    "/api/auth/logout",
    "/api/auth/bootstrap",
}


@app.middleware("http")
async def require_auth_middleware(request: Request, call_next):
    if not auth_required():
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path.rstrip("/") or "/"
    if path in PUBLIC_API_PATHS:
        return await call_next(request)
    auth_header = request.headers.get("Authorization", "")
    token = (
        auth_header.removeprefix("Bearer ").strip()
        if auth_header.startswith("Bearer ")
        else None
    )
    if not get_user_from_token(token):
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})
    return await call_next(request)


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


class ChainProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1)


class ChainedUserCreate(BaseModel):
    user_key: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    role: str = "driver"
    api_url: str | None = None
    contact: str | None = None
    status: str = "active"
    notes: str | None = None


class ChainedUserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    api_url: str | None = None
    contact: str | None = None
    status: str | None = None
    notes: str | None = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class BootstrapUserRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    display_name: str | None = None
    role: str = "admin"


class CompPlanFlag(BaseModel):
    level: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CompPlanScenario(BaseModel):
    scenario_type: str = "base"
    weekly_miles: float = 0
    weekly_hours: float = 0
    loaded_miles: float = 0
    empty_miles: float = 0
    gross_pay_weekly: float = 0
    accessorials_weekly: float = 0
    bonuses_weekly: float = 0
    benefits_value_weekly: float = 0
    payroll_tax_weekly: float = 0
    income_tax_reserve_weekly: float = 0
    self_employment_tax_weekly: float = 0
    health_insurance_weekly: float = 0
    retirement_weekly: float = 0
    truck_payment_weekly: float = 0
    trailer_rental_weekly: float = 0
    maintenance_escrow_weekly: float = 0
    performance_escrow_weekly: float = 0
    insurance_weekly: float = 0
    fuel_weekly: float = 0
    tolls_weekly: float = 0
    admin_fees_weekly: float = 0
    carrier_percentage: float = 0
    other_deductions_weekly: float = 0
    downtime_reserve_weekly: float = 0


class CompPlanCreate(BaseModel):
    company_name: str = Field(min_length=1)
    position_type: str = Field(min_length=1)
    pay_method: str = "mixed"
    home_time_notes: str | None = None
    notes: str | None = None
    flags: list[CompPlanFlag] = Field(default_factory=list)
    scenarios: list[CompPlanScenario] = Field(default_factory=list)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "road-hawk",
        "version": package_version(),
        "git_revision": git_revision(),
        "product": PRODUCT,
        "brand": BRAND,
        "company": COMPANY_LEGAL,
        "company_short": COMPANY_SHORT,
        "copyright": COPYRIGHT_NOTICE,
        "trademark_footer": TRADEMARK_FOOTER_SHORT,
        "copyright_trademark_notice": COPYRIGHT_TRADEMARK_NOTICE,
        "copyright_trademark_notice_legal": COPYRIGHT_TRADEMARK_NOTICE_LEGAL,
        "privacy_notice": PRIVACY_NOTICE_ROAD_HAWK_TITLE,
        "privacy_footer": PRIVACY_FOOTER_SHORT,
        "contact": {
            "organizations": CONTACT_ORGANIZATIONS,
            "location": CONTACT_LOCATION,
            "timezone": CONTACT_TIMEZONE,
            "timezone_label": CONTACT_TIMEZONE_LABEL,
            "email": CONTACT_EMAIL,
            "phone": CONTACT_PHONE,
            "phone_url": CONTACT_PHONE_URL,
            "hours": CONTACT_HOURS,
            "website": CONTACT_WEBSITE,
            "links": CONTACT_LINKS,
        },
        "brand_assets_source": BRAND_ASSETS_SOURCE,
        "mode": deploy_mode(),
        "api_url": api_url(),
        "auth_required": auth_required(),
        "connection_modes": connection_modes(),
    }


@app.get("/api/connection")
def connection_info() -> dict[str, Any]:
    return {
        "mode": deploy_mode(),
        "connection_modes": connection_modes(),
        "api_url": api_url(),
        "api_host": api_host(),
        "api_port": api_port(),
        "auth_required": auth_required(),
        "roles": sorted(APP_ROLES),
        "server_hint": (
            "Set ROAD_HAWK_MODE=server, ROAD_HAWK_API_HOST=0.0.0.0, and "
            "ROAD_HAWK_AUTH_REQUIRED=1 to accept remote logins."
        ),
        "client_hint": (
            "Set dashboard connection mode to Remote client and enter this server's API URL."
        ),
    }


@app.get("/api/auth/status")
def get_auth_status(authorization: Annotated[str | None, Header()] = None) -> dict:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    return auth_status(token)


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict:
    try:
        user = authenticate_user(payload.username, payload.password)
        session = create_session(user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": user,
    }


@app.post("/api/auth/logout")
def logout(authorization: Annotated[str | None, Header()] = None) -> dict:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    revoke_session(token)
    return {"message": "Logged out"}


@app.post("/api/auth/bootstrap", status_code=201)
def bootstrap_first_user(payload: BootstrapUserRequest) -> dict:
    from .database import connect

    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM app_users").fetchone()["count"]
    if count:
        raise HTTPException(status_code=400, detail="Users already exist")

    try:
        user = create_user(
            username=payload.username,
            password=payload.password,
            role=payload.role,
            display_name=payload.display_name,
        )
        session = create_session(user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
        },
        "message": "Initial admin user created",
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
def export_trips() -> FileResponse:
    path = export_trips_csv()
    return FileResponse(
        path,
        media_type="text/csv; charset=utf-8",
        filename="trips_export.csv",
    )


@app.post("/api/import/trips")
async def import_trips(file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")

    try:
        return import_trips_csv(file.file, filename=file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
def export_documents() -> FileResponse:
    path = export_documents_csv()
    return FileResponse(
        path,
        media_type="text/csv; charset=utf-8",
        filename="documents_export.csv",
    )


@app.get("/api/chain/profile")
def chain_profile() -> dict:
    return {
        **get_chain_profile(),
        "roles": sorted(CHAIN_ROLES),
        "statuses": sorted(CHAIN_STATUSES),
    }


@app.put("/api/chain/profile")
def update_profile(payload: ChainProfileUpdate) -> dict:
    try:
        return update_chain_profile(display_name=payload.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/chain/users")
def chained_users() -> list[dict]:
    return list_chained_users()


@app.post("/api/chain/users", status_code=201)
def create_chained_user(payload: ChainedUserCreate) -> dict:
    try:
        return add_chained_user(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/chain/users/{chained_id}")
def patch_chained_user(chained_id: int, payload: ChainedUserUpdate) -> dict:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return update_chained_user(chained_id, **fields)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@app.delete("/api/chain/users/{chained_id}", status_code=204)
def delete_chained_user(chained_id: int) -> None:
    try:
        remove_chained_user(chained_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/comp-plans/meta")
def comp_plans_meta() -> dict:
    return {
        "position_types": sorted(POSITION_TYPES),
        "pay_methods": sorted(PAY_METHODS),
        "scenario_types": sorted(SCENARIO_TYPES),
        "disclaimer": ESTIMATE_DISCLAIMER,
    }


@app.get("/api/comp-plans")
def comp_plans_list() -> list[dict]:
    return list_comp_plans()


@app.post("/api/comp-plans", status_code=201)
def comp_plans_create(payload: CompPlanCreate) -> dict:
    body = payload.model_dump()
    if not body["scenarios"]:
        body["scenarios"] = [CompPlanScenario().model_dump()]
    try:
        return create_comp_plan(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/comp-plans/compare/ranked")
def comp_plans_compare(
    ids: str,
    scenario: str = "base",
) -> dict:
    try:
        plan_ids = [int(value.strip()) for value in ids.split(",") if value.strip()]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid plan ids") from exc
    if not plan_ids:
        raise HTTPException(status_code=400, detail="At least one plan id is required")
    try:
        ranked = compare_comp_plans(plan_ids, scenario_type=scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "scenario": scenario,
        "disclaimer": ESTIMATE_DISCLAIMER,
        "results": ranked,
    }


@app.post("/api/comp-plans/import")
async def comp_plans_import(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSV file required")
    try:
        return import_comp_plans_csv(file.file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/comp-plans/export")
def comp_plans_export() -> FileResponse:
    path = export_comp_plans_csv()
    return FileResponse(
        path,
        media_type="text/csv; charset=utf-8",
        filename="comp_plans_export.csv",
    )


@app.get("/api/comp-plans/{plan_id}")
def comp_plans_detail(plan_id: int) -> dict:
    try:
        return get_comp_plan(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/comp-plans/{plan_id}", status_code=204)
def comp_plans_delete(plan_id: int) -> None:
    try:
        delete_comp_plan(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc