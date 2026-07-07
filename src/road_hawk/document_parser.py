"""Heuristic field parser for trucking paperwork."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .document_types import DOCUMENT_TYPES, PARSED_FIELD_NAMES, PARSER_VERSION

DATE_PATTERN = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)

MONEY_PATTERN = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)")
GALLON_PATTERN = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*(?:gal(?:lons)?|gals?))|(?:gallons?\s*[:#]?\s*(\d+(?:\.\d+)?))",
    re.IGNORECASE,
)

TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "bol": ("bill of lading", "b/l", "bol", "shipper", "consignee"),
    "pod": ("proof of delivery", "pod", "delivered", "receiver signature", "signed by"),
    "rate_confirmation": ("rate confirmation", "rate conf", "linehaul", "all-in rate", "rpm"),
    "fuel_receipt": ("fuel", "diesel", "gallons", "pump", "fuel receipt"),
    "scale_ticket": ("scale", "gross", "tare", "net weight", "weigh"),
    "lumper_receipt": ("lumper", "unloading fee", "lump"),
    "repair_invoice": ("repair", "service invoice", "parts", "labor", "maintenance"),
    "registration_insurance": ("registration", "insurance", "policy", "vin", "plate"),
    "broker_screenshot": ("dat", "truckstop", "load board", "broker", "posted rate"),
}

FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "load_number": re.compile(
        r"(?:load\s*(?:#|no\.?|number)|pro\s*#?|reference)\s*[:#]?\s*([A-Z0-9-]{4,})",
        re.IGNORECASE,
    ),
    "trip_reference": re.compile(
        r"(?:trip\s*(?:#|no\.?|ref)|trip\s*id)\s*[:#]?\s*([A-Z0-9-]{3,})",
        re.IGNORECASE,
    ),
    "driver_id": re.compile(r"(?:driver\s*(?:#|id|name))\s*[:#]?\s*([A-Z0-9-]{2,})", re.IGNORECASE),
    "truck_number": re.compile(
        r"(?:truck\s*(?:#|no\.?|number|unit))\s*[:#]?\s*([A-Z0-9-]{2,})",
        re.IGNORECASE,
    ),
    "trailer_number": re.compile(
        r"(?:trailer\s*(?:#|no\.?|number|unit))\s*[:#]?\s*([A-Z0-9-]{2,})",
        re.IGNORECASE,
    ),
    "broker": re.compile(r"(?:broker|dispatch(?:er)?)\s*[:#]?\s*([^\n\r]{3,60})", re.IGNORECASE),
    "carrier": re.compile(r"(?:carrier|motor carrier)\s*[:#]?\s*([^\n\r]{3,60})", re.IGNORECASE),
    "shipper": re.compile(r"(?:shipper|origin)\s*[:#]?\s*([^\n\r]{3,80})", re.IGNORECASE),
    "receiver": re.compile(
        r"(?:receiver|consignee|destination)\s*[:#]?\s*([^\n\r]{3,80})",
        re.IGNORECASE,
    ),
    "pickup_location": re.compile(
        r"(?:pickup|pick\s*up|origin)\s*(?:location|address)?\s*[:#]?\s*([^\n\r]{3,100})",
        re.IGNORECASE,
    ),
    "delivery_location": re.compile(
        r"(?:delivery|deliver\s*to|destination)\s*(?:location|address)?\s*[:#]?\s*([^\n\r]{3,100})",
        re.IGNORECASE,
    ),
    "miles": re.compile(r"(?:(\d+(?:\.\d+)?)\s*miles?)|(?:miles?\s*[:#]?\s*(\d+(?:\.\d+)?))", re.IGNORECASE),
    "rate": re.compile(
        r"(?:rate|linehaul|all[- ]in)\s*[:#]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        re.IGNORECASE,
    ),
    "accessorials": re.compile(r"(?:accessorials?|detention|layover)\s*[:#]?\s*([^\n\r]{3,80})", re.IGNORECASE),
    "fuel_cost": re.compile(
        r"(?:fuel\s*(?:cost|total)|total\s*(?:fuel|sale))\s*[:#]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        re.IGNORECASE,
    ),
    "receipt_total": re.compile(
        r"(?:total|amount\s*due|grand\s*total)\s*[:#]?\s*\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
        re.IGNORECASE,
    ),
    "service_description": re.compile(
        r"(?:service|repair|work\s*performed|description)\s*[:#]?\s*([^\n\r]{3,120})",
        re.IGNORECASE,
    ),
    "pod_signature_status": re.compile(
        r"(?:signature|signed|pod\s*status)\s*[:#]?\s*([^\n\r]{3,60})",
        re.IGNORECASE,
    ),
}


@dataclass
class ParsedField:
    field_name: str
    extracted_value: str
    confidence: float


@dataclass
class ParseResult:
    document_type: str
    fields: list[ParsedField]
    notes: str
    needs_review: bool


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :-#")


def classify_document_type(text: str) -> tuple[str, float]:
    lowered = text.lower()
    scores: dict[str, int] = {doc_type: 0 for doc_type in DOCUMENT_TYPES}
    for doc_type, keywords in TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[doc_type] += 1
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    if best_score == 0:
        return "unknown", 0.35
    confidence = min(0.95, 0.45 + (best_score * 0.1))
    return best_type, round(confidence, 2)


def _first_money(text: str) -> str | None:
    match = MONEY_PATTERN.search(text)
    return match.group(1).replace(",", "") if match else None


def _first_gallons(text: str) -> str | None:
    match = GALLON_PATTERN.search(text)
    if not match:
        return None
    return match.group(1) or match.group(2)


def _first_date(text: str) -> str | None:
    match = DATE_PATTERN.search(text)
    return match.group(0) if match else None


def parse_document_fields(raw_text: str, hinted_type: str | None = None) -> ParseResult:
    text = raw_text.strip()
    notes: list[str] = []
    needs_review = False

    if not text:
        return ParseResult(
            document_type=hinted_type or "unknown",
            fields=[],
            notes="No extractable text to parse.",
            needs_review=True,
        )

    doc_type, type_confidence = classify_document_type(text)
    if hinted_type and hinted_type in DOCUMENT_TYPES and hinted_type != "unknown":
        doc_type = hinted_type
        type_confidence = max(type_confidence, 0.55)

    fields: list[ParsedField] = [
        ParsedField("document_type", doc_type, type_confidence),
    ]

    document_date = _first_date(text)
    if document_date:
        fields.append(ParsedField("document_date", document_date, 0.7))
    else:
        needs_review = True
        notes.append("Document date not detected.")

    for field_name, pattern in FIELD_PATTERNS.items():
        match = pattern.search(text)
        if not match:
            continue
        captured = next((group for group in match.groups() if group), None)
        value = _clean(captured or "")
        if value:
            fields.append(ParsedField(field_name, value, 0.72))

    gallons = _first_gallons(text)
    if gallons and not any(f.field_name == "fuel_gallons" for f in fields):
        fields.append(ParsedField("fuel_gallons", gallons, 0.68))

    if doc_type in {"fuel_receipt", "scale_ticket", "lumper_receipt", "repair_invoice"}:
        if not any(f.field_name == "receipt_total" for f in fields):
            total = _first_money(text)
            if total:
                fields.append(ParsedField("receipt_total", total, 0.6))

    # Conflict checks: multiple distinct load numbers
    load_values = {f.extracted_value for f in fields if f.field_name == "load_number"}
    if len(load_values) > 1:
        needs_review = True
        notes.append("Conflicting load numbers detected.")

    if type_confidence < 0.5:
        needs_review = True
        notes.append("Document type classification is uncertain.")

    if len(fields) <= 2:
        needs_review = True
        notes.append("Few structured fields parsed; driver review recommended.")

    remainder = text
    known_values = {f.extracted_value for f in fields if f.extracted_value}
    for value in known_values:
        remainder = remainder.replace(value, " ")
    remainder = _clean(remainder)
    if len(remainder) > 40:
        fields.append(ParsedField("notes", remainder[:500], 0.4))

    return ParseResult(
        document_type=doc_type,
        fields=fields,
        notes="; ".join(notes) if notes else f"Parsed with {PARSER_VERSION}.",
        needs_review=needs_review,
    )


def fields_to_dict(fields: list[ParsedField]) -> dict[str, str]:
    return {field.field_name: field.extracted_value for field in fields if field.field_name in PARSED_FIELD_NAMES}