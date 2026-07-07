"""Coyote Round 2 document intake services."""

from __future__ import annotations

import csv
import re
import shutil
from pathlib import Path
from typing import BinaryIO

from .database import connect, data_dir, uploads_dir
from .services import ensure_driver, ensure_truck
from .document_extraction import extract_document_text
from .document_parser import PARSER_VERSION, parse_document_fields
from .document_types import (
    DOCUMENT_TYPES,
    EXTRACTION_METHODS,
    PARSED_FIELD_NAMES,
    SOURCE_TYPES,
    VERIFICATION_STATUSES,
)

_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitize_filename(name: str) -> str:
    cleaned = _FILENAME_SAFE.sub("_", Path(name).name).strip("._")
    return cleaned or "document"


def _touch_document(conn, document_id: int) -> None:
    conn.execute(
        "UPDATE documents SET updated_at = datetime('now') WHERE id = ?",
        (document_id,),
    )


def _fetch_document_row(document_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
    return dict(row) if row else None


def _latest_extraction(conn, document_id: int) -> dict | None:
    row = conn.execute(
        """
        SELECT * FROM document_extractions
        WHERE document_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (document_id,),
    ).fetchone()
    return dict(row) if row else None


def _list_fields(conn, document_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, document_id, field_name, extracted_value, corrected_value,
               confidence, verified, created_at, updated_at
        FROM document_fields
        WHERE document_id = ?
        ORDER BY field_name
        """,
        (document_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _store_fields(
    conn,
    document_id: int,
    *,
    fields: list,
    verified: bool = False,
) -> None:
    for field in fields:
        conn.execute(
            """
            INSERT INTO document_fields (
                document_id, field_name, extracted_value, corrected_value,
                confidence, verified
            ) VALUES (?, ?, ?, NULL, ?, ?)
            ON CONFLICT(document_id, field_name) DO UPDATE SET
                extracted_value = excluded.extracted_value,
                confidence = excluded.confidence,
                verified = excluded.verified,
                updated_at = datetime('now')
            """,
            (
                document_id,
                field.field_name,
                field.extracted_value,
                field.confidence,
                1 if verified else 0,
            ),
        )


def _resolve_verification_status(
    *,
    extraction_needs_review: bool,
    parse_needs_review: bool,
    extraction_method: str,
) -> str:
    if extraction_method == "failed":
        return "needs_review"
    if extraction_needs_review or parse_needs_review:
        return "needs_review"
    return "unverified"


def ingest_document(
    file_obj: BinaryIO,
    *,
    original_filename: str,
    mime_type: str | None = None,
    source_type: str = "upload",
    driver_id: str | None = None,
    truck_number: str | None = None,
    load_number: str | None = None,
    document_type_hint: str | None = None,
) -> dict:
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Invalid source_type: {source_type}")

    if driver_id:
        ensure_driver(driver_id.strip(), driver_id.strip())
    if truck_number:
        ensure_truck(truck_number.strip())

    safe_name = _sanitize_filename(original_filename)

    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO documents (
                document_type, original_filename, stored_path, mime_type,
                source_type, extraction_method, verification_status,
                driver_id, truck_number, load_number
            ) VALUES ('unknown', ?, 'pending', ?, ?, 'manual', 'unverified', ?, ?, ?)
            """,
            (
                original_filename,
                mime_type,
                source_type,
                driver_id,
                truck_number,
                load_number,
            ),
        )
        document_id = cursor.lastrowid

        doc_dir = uploads_dir() / str(document_id)
        doc_dir.mkdir(parents=True, exist_ok=True)
        stored_path = doc_dir / safe_name

        with stored_path.open("wb") as handle:
            shutil.copyfileobj(file_obj, handle)

        conn.execute(
            "UPDATE documents SET stored_path = ? WHERE id = ?",
            (str(stored_path), document_id),
        )

    return process_document_extraction(
        document_id,
        document_type_hint=document_type_hint,
    )


def process_document_extraction(
    document_id: int,
    *,
    document_type_hint: str | None = None,
) -> dict:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")

    stored_path = Path(document["stored_path"])
    if not stored_path.exists():
        raise ValueError(f"Original file missing for document {document_id}")

    extraction = extract_document_text(stored_path, document.get("mime_type"))
    parse_result = parse_document_fields(
        extraction.raw_text,
        hinted_type=document_type_hint or document.get("document_type"),
    )

    verification_status = _resolve_verification_status(
        extraction_needs_review=extraction.needs_review,
        parse_needs_review=parse_result.needs_review,
        extraction_method=extraction.method,
    )

    load_number = document.get("load_number")
    for field in parse_result.fields:
        if field.field_name == "load_number" and not load_number:
            load_number = field.extracted_value

    extraction_notes = "; ".join(
        part
        for part in (extraction.notes, parse_result.notes)
        if part
    )

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO document_extractions (
                document_id, raw_text, ocr_confidence, parser_version, extraction_notes
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                document_id,
                extraction.raw_text,
                extraction.ocr_confidence,
                PARSER_VERSION,
                extraction_notes,
            ),
        )

        conn.execute(
            """
            UPDATE documents
            SET document_type = ?,
                extraction_method = ?,
                verification_status = ?,
                load_number = COALESCE(?, load_number),
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                parse_result.document_type,
                extraction.method,
                verification_status,
                load_number,
                document_id,
            ),
        )

        _store_fields(conn, document_id, fields=parse_result.fields, verified=False)

    return get_document(document_id)


def list_documents(
    *,
    driver_id: str | None = None,
    verification_status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    query = """
        SELECT id, document_type, original_filename, mime_type, source_type,
               extraction_method, verification_status, driver_id, truck_number,
               load_number, created_at, updated_at
        FROM documents
    """
    clauses: list[str] = []
    params: list = []

    if driver_id:
        clauses.append("driver_id = ?")
        params.append(driver_id.strip())
    if verification_status:
        clauses.append("verification_status = ?")
        params.append(verification_status)

    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with connect() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def get_document(document_id: int) -> dict:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")

    with connect() as conn:
        extraction = _latest_extraction(conn, document_id)
        fields = _list_fields(conn, document_id)

    return {
        "document": document,
        "extraction": extraction,
        "fields": fields,
    }


def verify_document(
    document_id: int,
    *,
    corrected_fields: dict[str, str],
    document_type: str | None = None,
) -> dict:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")

    if document_type and document_type not in DOCUMENT_TYPES:
        raise ValueError(f"Invalid document_type: {document_type}")

    resolved_driver = corrected_fields.get("driver_id") or document.get("driver_id")
    resolved_truck = corrected_fields.get("truck_number") or document.get("truck_number")
    if resolved_driver:
        ensure_driver(resolved_driver.strip(), resolved_driver.strip())
    if resolved_truck:
        ensure_truck(resolved_truck.strip())

    with connect() as conn:
        for field_name, value in corrected_fields.items():
            if field_name not in PARSED_FIELD_NAMES:
                continue
            conn.execute(
                """
                INSERT INTO document_fields (
                    document_id, field_name, extracted_value, corrected_value,
                    confidence, verified
                ) VALUES (?, ?, NULL, ?, 1.0, 1)
                ON CONFLICT(document_id, field_name) DO UPDATE SET
                    corrected_value = excluded.corrected_value,
                    verified = 1,
                    updated_at = datetime('now')
                """,
                (document_id, field_name, value.strip()),
            )

        resolved_type = document_type or document.get("document_type") or "unknown"
        load_number = corrected_fields.get("load_number") or document.get("load_number")
        driver_id = corrected_fields.get("driver_id") or document.get("driver_id")
        truck_number = corrected_fields.get("truck_number") or document.get("truck_number")

        conn.execute(
            """
            UPDATE documents
            SET document_type = ?,
                verification_status = 'verified',
                load_number = ?,
                driver_id = COALESCE(?, driver_id),
                truck_number = COALESCE(?, truck_number),
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (resolved_type, load_number, driver_id, truck_number, document_id),
        )

    return get_document(document_id)


def reject_document(
    document_id: int,
    *,
    reason: str | None = None,
    status: str = "needs_review",
) -> dict:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")

    if status not in {"rejected", "needs_review"}:
        raise ValueError(f"Invalid reject status: {status}")

    note = reason or (
        "Marked rejected by driver." if status == "rejected" else "Marked for manual review by driver."
    )

    with connect() as conn:
        conn.execute(
            """
            UPDATE documents
            SET verification_status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (status, document_id),
        )
        prior = _latest_extraction(conn, document_id)
        conn.execute(
            """
            INSERT INTO document_extractions (
                document_id, raw_text, ocr_confidence, parser_version, extraction_notes
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                document_id,
                prior["raw_text"] if prior else "",
                prior.get("ocr_confidence") if prior else None,
                PARSER_VERSION,
                note,
            ),
        )

    return get_document(document_id)


def reprocess_document(document_id: int, *, document_type_hint: str | None = None) -> dict:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")

    with connect() as conn:
        conn.execute(
            """
            UPDATE documents
            SET verification_status = 'unverified', updated_at = datetime('now')
            WHERE id = ?
            """,
            (document_id,),
        )
        conn.execute(
            "UPDATE document_fields SET verified = 0, updated_at = datetime('now') WHERE document_id = ?",
            (document_id,),
        )

    return process_document_extraction(document_id, document_type_hint=document_type_hint)


def get_document_file_path(document_id: int) -> Path:
    document = _fetch_document_row(document_id)
    if not document:
        raise ValueError(f"Document {document_id} not found")
    path = Path(document["stored_path"])
    if not path.exists():
        raise ValueError(f"Original file missing for document {document_id}")
    return path


def export_documents_csv(path: Path | None = None) -> Path:
    export_path = path or (data_dir() / "documents_export.csv")
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.document_type, d.original_filename, d.mime_type,
                   d.source_type, d.extraction_method, d.verification_status,
                   d.driver_id, d.truck_number, d.load_number,
                   d.created_at, d.updated_at,
                   f.field_name, f.extracted_value, f.corrected_value, f.verified
            FROM documents d
            LEFT JOIN document_fields f ON f.document_id = d.id
            ORDER BY d.created_at DESC, d.id, f.field_name
            """
        ).fetchall()

    fieldnames = [
        "id",
        "document_type",
        "original_filename",
        "mime_type",
        "source_type",
        "extraction_method",
        "verification_status",
        "driver_id",
        "truck_number",
        "load_number",
        "created_at",
        "updated_at",
        "field_name",
        "extracted_value",
        "corrected_value",
        "verified",
    ]
    with export_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in fieldnames})

    return export_path