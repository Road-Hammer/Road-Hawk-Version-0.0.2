"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export function ExportButton() {
  const [message, setMessage] = useState<string | null>(null);

  async function onExport() {
    try {
      const result = await api.exportTrips();
      setMessage(result.message);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Export failed");
    }
  }

  return (
    <div className="flex items-center gap-3">
      <button className="btn-secondary" type="button" onClick={onExport}>
        Export trips CSV
      </button>
      {message ? <span className="text-sm text-road-muted">{message}</span> : null}
    </div>
  );
}