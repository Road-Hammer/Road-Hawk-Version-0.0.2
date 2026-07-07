import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from road_hawk import database, document_services, services  # noqa: E402
from road_hawk.api import app  # noqa: E402
from road_hawk.document_extraction import ExtractionResult  # noqa: E402


@pytest.fixture
def client(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    with TestClient(app) as test_client:
        yield test_client
    database.set_data_root(None)


@pytest.fixture
def isolated_data_root(tmp_path: Path):
    database.set_data_root(tmp_path)
    services.bootstrap()
    yield tmp_path
    database.set_data_root(None)


SAMPLE_BOL = """\
BILL OF LADING
Load #: RH-LOAD-4421
Driver ID: RH-001
Truck #: T-101
Trailer #: TR-55
Shipper: Acme Warehouse, Dallas TX
Receiver: Midwest DC, Chicago IL
Pickup location: Dallas, TX
Delivery location: Chicago, IL
Miles: 920
Rate: $2,450.00
Date: 07/07/2026
"""


def test_document_record_creation_via_direct_text(client: TestClient, isolated_data_root: Path) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": ("bol_sample.txt", SAMPLE_BOL.encode("utf-8"), "text/plain")},
        data={
            "source_type": "upload",
            "driver_id": "RH-001",
            "truck_number": "T-101",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    document = payload["document"]
    assert document["verification_status"] == "unverified"
    assert document["extraction_method"] == "direct_text"
    assert payload["extraction"]["raw_text"]
    assert Path(document["stored_path"]).exists()
    assert Path(document["stored_path"]).read_text(encoding="utf-8") == SAMPLE_BOL

    field_map = {field["field_name"]: field for field in payload["fields"]}
    assert field_map["load_number"]["extracted_value"] == "RH-LOAD-4421"
    assert field_map["load_number"]["verified"] == 0


def test_direct_text_extraction_path(isolated_data_root: Path) -> None:
    content = b"Fuel receipt\nGallons: 62.5\nTotal: $245.10\nDate: 07/01/2026"
    result = document_services.ingest_document(
        io.BytesIO(content),
        original_filename="fuel.txt",
        mime_type="text/plain",
        source_type="upload",
    )
    assert result["document"]["extraction_method"] == "direct_text"
    assert "Fuel" in result["extraction"]["raw_text"]


def test_ocr_fallback_path_can_be_mocked(isolated_data_root: Path) -> None:
    fake_png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    mocked = ExtractionResult(
        raw_text="Load #: MOCK-9001\nTruck #: T-202",
        method="ocr",
        ocr_confidence=48.0,
        notes="Mocked OCR for test.",
        needs_review=True,
    )

    with patch("road_hawk.document_services.extract_document_text", return_value=mocked):
        result = document_services.ingest_document(
            io.BytesIO(fake_png),
            original_filename="scan.png",
            mime_type="image/png",
            source_type="scan",
        )

    assert result["document"]["extraction_method"] == "ocr"
    assert result["document"]["verification_status"] == "needs_review"
    assert result["extraction"]["ocr_confidence"] == 48.0


def test_low_confidence_returns_needs_review(isolated_data_root: Path) -> None:
    mocked = ExtractionResult(
        raw_text="",
        method="failed",
        ocr_confidence=None,
        notes="OCR engine not installed.",
        needs_review=True,
    )
    with patch("road_hawk.document_services.extract_document_text", return_value=mocked):
        result = document_services.ingest_document(
            io.BytesIO(b"fake-image"),
            original_filename="blurry.jpg",
            mime_type="image/jpeg",
            source_type="camera",
        )
    assert result["document"]["verification_status"] == "needs_review"


def test_driver_verification_updates_corrected_fields(client: TestClient) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("bol_sample.txt", SAMPLE_BOL.encode("utf-8"), "text/plain")},
        data={"driver_id": "RH-001"},
    )
    document_id = upload.json()["document"]["id"]

    verify = client.post(
        f"/api/documents/{document_id}/verify",
        json={
            "document_type": "bol",
            "corrected_fields": {
                "load_number": "RH-LOAD-4421-CORRECTED",
                "driver_id": "RH-001",
                "truck_number": "T-101",
            },
        },
    )
    assert verify.status_code == 200
    payload = verify.json()
    assert payload["document"]["verification_status"] == "verified"

    field_map = {field["field_name"]: field for field in payload["fields"]}
    assert field_map["load_number"]["corrected_value"] == "RH-LOAD-4421-CORRECTED"
    assert field_map["load_number"]["verified"] == 1


def test_original_document_path_is_preserved(client: TestClient, isolated_data_root: Path) -> None:
    original = b"Preserve this original file body."
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("preserve_me.txt", original, "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    stored_path = Path(upload.json()["document"]["stored_path"])

    reprocess = client.post(f"/api/documents/{document_id}/reprocess", json={})
    assert reprocess.status_code == 200
    assert stored_path.exists()
    assert stored_path.read_bytes() == original


def test_export_preserves_verification_status(client: TestClient, isolated_data_root: Path) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("bol_sample.txt", SAMPLE_BOL.encode("utf-8"), "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    client.post(
        f"/api/documents/{document_id}/verify",
        json={"corrected_fields": {"load_number": "RH-LOAD-4421"}},
    )

    export_path = document_services.export_documents_csv()
    csv_text = export_path.read_text(encoding="utf-8")
    assert "verification_status" in csv_text
    assert "verified" in csv_text
    assert str(document_id) in csv_text


def test_reject_marks_needs_review(client: TestClient) -> None:
    upload = client.post(
        "/api/documents/upload",
        files={"file": ("bol_sample.txt", SAMPLE_BOL.encode("utf-8"), "text/plain")},
    )
    document_id = upload.json()["document"]["id"]
    response = client.post(
        f"/api/documents/{document_id}/reject",
        json={"reason": "Fields look wrong"},
    )
    assert response.status_code == 200
    assert response.json()["document"]["verification_status"] == "needs_review"