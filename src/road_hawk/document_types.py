"""Constants for Coyote Round 2 document intake."""

from __future__ import annotations

PARSER_VERSION = "coyote-r2-v1"

DOCUMENT_TYPES = (
    "bol",
    "pod",
    "rate_confirmation",
    "fuel_receipt",
    "scale_ticket",
    "lumper_receipt",
    "repair_invoice",
    "registration_insurance",
    "broker_screenshot",
    "unknown",
)

SOURCE_TYPES = ("upload", "camera", "scan", "screenshot", "email", "other")

EXTRACTION_METHODS = ("direct_text", "ocr", "manual", "failed")

VERIFICATION_STATUSES = ("unverified", "verified", "rejected", "needs_review")

PARSED_FIELD_NAMES = (
    "document_type",
    "document_date",
    "load_number",
    "trip_reference",
    "driver_id",
    "truck_number",
    "trailer_number",
    "broker",
    "carrier",
    "shipper",
    "receiver",
    "pickup_location",
    "delivery_location",
    "miles",
    "rate",
    "accessorials",
    "fuel_gallons",
    "fuel_cost",
    "receipt_total",
    "service_description",
    "pod_signature_status",
    "notes",
)

IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff",
    }
)

TEXT_MIME_TYPES = frozenset({"text/plain", "text/csv"})

DOCUMENT_TYPE_LABELS = {
    "bol": "Bill of Lading / BOL",
    "pod": "Proof of Delivery / POD",
    "rate_confirmation": "Rate Confirmation",
    "fuel_receipt": "Fuel Receipt",
    "scale_ticket": "Scale Ticket",
    "lumper_receipt": "Lumper Receipt",
    "repair_invoice": "Repair Invoice",
    "registration_insurance": "Registration / Insurance",
    "broker_screenshot": "Broker / Load-Board Screenshot",
    "unknown": "Unknown Document",
}