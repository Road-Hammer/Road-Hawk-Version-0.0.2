"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";
import {
  api,
  type DocumentDetail,
  type DocumentField,
  type DocumentSummary,
} from "@/lib/api";

const DOCUMENT_TYPES = [
  { value: "", label: "Auto-detect" },
  { value: "bol", label: "Bill of Lading / BOL" },
  { value: "pod", label: "Proof of Delivery / POD" },
  { value: "rate_confirmation", label: "Rate Confirmation" },
  { value: "fuel_receipt", label: "Fuel Receipt" },
  { value: "scale_ticket", label: "Scale Ticket" },
  { value: "lumper_receipt", label: "Lumper Receipt" },
  { value: "repair_invoice", label: "Repair Invoice" },
  { value: "registration_insurance", label: "Registration / Insurance" },
  { value: "broker_screenshot", label: "Broker / Load-Board Screenshot" },
  { value: "unknown", label: "Unknown Document" },
];

const SOURCE_TYPES = [
  { value: "upload", label: "Upload" },
  { value: "camera", label: "Camera capture" },
  { value: "scan", label: "Scan" },
  { value: "screenshot", label: "Screenshot" },
  { value: "email", label: "Email attachment" },
  { value: "other", label: "Other" },
];

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    unverified: "bg-amber-500/15 text-amber-300",
    verified: "bg-emerald-500/15 text-emerald-300",
    rejected: "bg-rose-500/15 text-rose-300",
    needs_review: "bg-sky-500/15 text-sky-300",
  };
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-medium ${styles[status] ?? "bg-white/10 text-slate-300"}`}
    >
      {status.replace("_", " ")}
    </span>
  );
}

function fieldValue(field: DocumentField) {
  return field.corrected_value ?? field.extracted_value ?? "";
}

export function DocumentIntake({ initialDocuments }: { initialDocuments: DocumentSummary[] }) {
  const router = useRouter();
  const [documents, setDocuments] = useState(initialDocuments);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [draftFields, setDraftFields] = useState<Record<string, string>>({});

  const selectedSummary = useMemo(
    () => documents.find((doc) => doc.id === selectedId) ?? null,
    [documents, selectedId],
  );

  async function refreshList() {
    const rows = await api.getDocuments(100);
    setDocuments(rows);
  }

  async function loadDetail(documentId: number) {
    setSelectedId(documentId);
    setError(null);
    const payload = await api.getDocument(documentId);
    setDetail(payload);
    const nextDraft: Record<string, string> = {};
    for (const field of payload.fields) {
      nextDraft[field.field_name] = fieldValue(field);
    }
    setDraftFields(nextDraft);
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      setError("Choose a document file first.");
      setBusy(false);
      return;
    }

    try {
      const uploaded = await api.uploadDocument(form);
      setMessage("Document uploaded. Review extracted fields before verifying.");
      await refreshList();
      await loadDetail(uploaded.document.id);
      event.currentTarget.reset();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const verified = await api.verifyDocument(detail.document.id, {
        document_type: draftFields.document_type || detail.document.document_type,
        corrected_fields: draftFields,
      });
      setDetail(verified);
      setMessage("Document verified by driver.");
      await refreshList();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onReject(rejected: boolean) {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.rejectDocument(detail.document.id, {
        rejected,
        reason: rejected ? "Driver rejected extraction." : "Driver flagged for manual review.",
      });
      setDetail(updated);
      setMessage(rejected ? "Document marked rejected." : "Document marked needs review.");
      await refreshList();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onReprocess() {
    if (!detail) return;
    setBusy(true);
    setError(null);
    try {
      const reprocessed = await api.reprocessDocument(detail.document.id, {});
      setDetail(reprocessed);
      const nextDraft: Record<string, string> = {};
      for (const field of reprocessed.fields) {
        nextDraft[field.field_name] = fieldValue(field);
      }
      setDraftFields(nextDraft);
      setMessage("Extraction reprocessed. Fields reset to unverified.");
      await refreshList();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reprocess failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <form onSubmit={onUpload} className="panel space-y-4">
        <h3 className="text-lg font-semibold text-white">Upload or capture document</h3>
        <p className="text-sm text-road-muted">
          Direct text is used when available. OCR runs only for images, scans, and image-only PDFs.
        </p>
        <input className="input" type="file" name="file" accept=".txt,.pdf,.png,.jpg,.jpeg,.webp" required />
        <div className="grid gap-4 md:grid-cols-2">
          <select className="input" name="source_type" defaultValue="upload">
            {SOURCE_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select className="input" name="document_type_hint" defaultValue="">
            {DOCUMENT_TYPES.map((option) => (
              <option key={option.value || "auto"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <input className="input" name="driver_id" placeholder="Driver ID (optional)" />
          <input className="input" name="truck_number" placeholder="Truck number (optional)" />
          <input className="input" name="load_number" placeholder="Load number (optional)" />
        </div>
        <button className="btn-primary" type="submit" disabled={busy}>
          {busy ? "Processing..." : "Upload document"}
        </button>
      </form>

      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
      {error ? <p className="text-sm text-rose-400">{error}</p> : null}

      <div className="panel">
        <h3 className="text-lg font-semibold text-white">Document queue</h3>
        <div className="table-shell mt-4">
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Type</th>
                <th>Method</th>
                <th>Status</th>
                <th>Driver</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-road-muted">
                    No documents yet. Upload paperwork to begin intake.
                  </td>
                </tr>
              ) : (
                documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.original_filename}</td>
                    <td>{doc.document_type}</td>
                    <td>{doc.extraction_method}</td>
                    <td>{statusBadge(doc.verification_status)}</td>
                    <td>{doc.driver_id ?? "—"}</td>
                    <td>{doc.created_at}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => loadDetail(doc.id)}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {detail && selectedSummary ? (
        <div className="panel space-y-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Review: {selectedSummary.original_filename}</h3>
              <p className="mt-1 text-sm text-road-muted">
                Method: {detail.document.extraction_method} · Status:{" "}
                {detail.document.verification_status}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="btn-secondary" onClick={onReprocess} disabled={busy}>
                Reprocess
              </button>
              <button type="button" className="btn-secondary" onClick={() => onReject(false)} disabled={busy}>
                Needs review
              </button>
              <button type="button" className="btn-secondary" onClick={() => onReject(true)} disabled={busy}>
                Reject
              </button>
              <button type="button" className="btn-primary" onClick={onVerify} disabled={busy}>
                Verify
              </button>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-road-amber">Raw extracted text</h4>
            <pre className="mt-2 max-h-56 overflow-auto rounded-xl border border-road-border bg-black/30 p-4 text-xs text-slate-300">
              {detail.extraction?.raw_text || "(no text extracted — manual entry required)"}
            </pre>
            {detail.extraction?.extraction_notes ? (
              <p className="mt-2 text-xs text-road-muted">{detail.extraction.extraction_notes}</p>
            ) : null}
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-semibold uppercase tracking-wide text-road-amber">
              Parsed fields (driver must verify)
            </h4>
            {detail.fields.length === 0 ? (
              <p className="text-sm text-road-muted">No parsed fields yet. Enter values manually before verifying.</p>
            ) : (
              detail.fields.map((field) => (
                <div key={field.id} className="grid gap-2 md:grid-cols-[220px_1fr] md:items-center">
                  <label className="text-sm text-road-muted" htmlFor={`field-${field.field_name}`}>
                    {field.field_name}
                    {field.confidence != null ? ` (${field.confidence})` : ""}
                  </label>
                  <input
                    id={`field-${field.field_name}`}
                    className="input"
                    value={draftFields[field.field_name] ?? ""}
                    onChange={(event) =>
                      setDraftFields((current) => ({
                        ...current,
                        [field.field_name]: event.target.value,
                      }))
                    }
                  />
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}