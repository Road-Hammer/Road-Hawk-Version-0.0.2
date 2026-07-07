"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, useRef, useState } from "react";
import { api } from "@/lib/api";

export function ExportButton() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<"export" | "import" | null>(null);

  async function onExport() {
    setBusy("export");
    setMessage(null);
    try {
      await api.exportTrips();
      setMessage("Trips CSV downloaded.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Export failed");
    } finally {
      setBusy(null);
    }
  }

  async function onImportSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    setBusy("import");
    setMessage(null);
    try {
      const result = await api.importTrips(file);
      const errorNote =
        result.errors.length > 0 ? ` ${result.errors.length} row(s) skipped.` : "";
      setMessage(`${result.message}${errorNote}`);
      router.refresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Import failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        className="btn-secondary"
        type="button"
        onClick={onExport}
        disabled={busy !== null}
      >
        {busy === "export" ? "Exporting..." : "Export trips CSV"}
      </button>
      <button
        className="btn-secondary"
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={busy !== null}
      >
        {busy === "import" ? "Importing..." : "Import trips CSV"}
      </button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={onImportSelected}
      />
      {message ? <span className="text-sm text-road-muted">{message}</span> : null}
    </div>
  );
}