"""Document text extraction: direct text first, OCR fallback when needed."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .document_types import IMAGE_MIME_TYPES, TEXT_MIME_TYPES

MIN_DIRECT_TEXT_CHARS = 20


@dataclass
class ExtractionResult:
    raw_text: str
    method: str
    ocr_confidence: float | None
    notes: str
    needs_review: bool


def _read_plain_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""

    reader = PdfReader(str(path))
    chunks: list[str] = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks).strip()


def _ocr_image(path: Path) -> tuple[str, float | None, str]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return (
            "",
            None,
            "OCR engine not installed. Install optional deps: pip install -e '.[ocr]' "
            "and system Tesseract. Manual entry required.",
        )

    try:
        image = Image.open(path)
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image).strip()
        confidences = [
            float(conf)
            for conf, word in zip(data.get("conf", []), data.get("text", []), strict=False)
            if word and str(conf).lstrip("-").isdigit() and int(conf) >= 0
        ]
        avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None
        if not text:
            return "", avg_conf, "OCR returned no readable text."
        return text, avg_conf, "OCR extraction completed."
    except Exception as exc:  # noqa: BLE001
        return "", None, f"OCR failed: {exc}"


def _ocr_pdf_pages(path: Path) -> tuple[str, float | None, str]:
    try:
        import fitz  # pymupdf
    except ImportError:
        return (
            "",
            None,
            "Image-only PDF detected. Install optional deps: pip install -e '.[ocr]' "
            "for page rendering + OCR, or enter fields manually.",
        )

    texts: list[str] = []
    confidences: list[float] = []
    notes: list[str] = []

    try:
        doc = fitz.open(str(path))
        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image_path = path.parent / f".ocr_page_{page_index}.png"
            pix.save(str(image_path))
            try:
                page_text, page_conf, page_note = _ocr_image(image_path)
                if page_text:
                    texts.append(page_text)
                if page_conf is not None:
                    confidences.append(page_conf)
                if page_note:
                    notes.append(page_note)
            finally:
                image_path.unlink(missing_ok=True)
        doc.close()
    except Exception as exc:  # noqa: BLE001
        return "", None, f"PDF OCR render failed: {exc}"

    combined = "\n\n".join(texts).strip()
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None
    note = "; ".join(notes) if notes else "PDF page OCR completed."
    return combined, avg_conf, note


def is_image_mime(mime_type: str | None) -> bool:
    if not mime_type:
        return False
    normalized = mime_type.lower().split(";")[0].strip()
    return normalized in IMAGE_MIME_TYPES


def is_pdf_mime(mime_type: str | None) -> bool:
    if not mime_type:
        return False
    return mime_type.lower().split(";")[0].strip() == "application/pdf"


def extract_document_text(path: Path, mime_type: str | None) -> ExtractionResult:
    """Extract text using direct methods first; OCR only when required."""
    normalized_mime = (mime_type or "").lower().split(";")[0].strip()
    suffix = path.suffix.lower()

    if normalized_mime in TEXT_MIME_TYPES or suffix in {".txt", ".csv"}:
        text = _read_plain_text(path)
        if text.strip():
            return ExtractionResult(
                raw_text=text,
                method="direct_text",
                ocr_confidence=None,
                notes="Plain text file read directly.",
                needs_review=False,
            )
        return ExtractionResult(
            raw_text="",
            method="failed",
            ocr_confidence=None,
            notes="Text file was empty.",
            needs_review=True,
        )

    if is_image_mime(normalized_mime) or suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}:
        text, confidence, note = _ocr_image(path)
        if text.strip():
            low_conf = confidence is not None and confidence < 55
            return ExtractionResult(
                raw_text=text,
                method="ocr",
                ocr_confidence=confidence,
                notes=note,
                needs_review=low_conf,
            )
        return ExtractionResult(
            raw_text="",
            method="failed" if "not installed" in note.lower() else "ocr",
            ocr_confidence=confidence,
            notes=note,
            needs_review=True,
        )

    if is_pdf_mime(normalized_mime) or suffix == ".pdf":
        direct_text = _extract_pdf_text(path)
        if len(direct_text) >= MIN_DIRECT_TEXT_CHARS:
            return ExtractionResult(
                raw_text=direct_text,
                method="direct_text",
                ocr_confidence=None,
                notes="Searchable PDF text extracted directly.",
                needs_review=False,
            )

        ocr_text, confidence, note = _ocr_pdf_pages(path)
        if ocr_text.strip():
            low_conf = confidence is not None and confidence < 55
            return ExtractionResult(
                raw_text=ocr_text,
                method="ocr",
                ocr_confidence=confidence,
                notes=f"Image-only PDF handled via OCR fallback. {note}",
                needs_review=low_conf,
            )

        return ExtractionResult(
            raw_text=direct_text,
            method="failed",
            ocr_confidence=confidence,
            notes=note or "PDF contained insufficient extractable text.",
            needs_review=True,
        )

    # Unknown format — attempt plain read, then OCR if it looks like an image path
    try:
        text = _read_plain_text(path)
        if len(text.strip()) >= MIN_DIRECT_TEXT_CHARS:
            return ExtractionResult(
                raw_text=text,
                method="direct_text",
                ocr_confidence=None,
                notes="Unknown MIME; read as text.",
                needs_review=False,
            )
    except OSError:
        pass

    return ExtractionResult(
        raw_text="",
        method="failed",
        ocr_confidence=None,
        notes=f"Unsupported document type ({mime_type or 'unknown'}). Manual entry required.",
        needs_review=True,
    )