"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export function TripForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      driver_id: String(form.get("driver_id") ?? ""),
      truck_number: String(form.get("truck_number") ?? ""),
      miles_driven: Number(form.get("miles_driven")),
      fuel_used: Number(form.get("fuel_used")),
      load_weight: form.get("load_weight") ? Number(form.get("load_weight")) : null,
      hours_driven: form.get("hours_driven") ? Number(form.get("hours_driven")) : null,
      fuel_price: form.get("fuel_price") ? Number(form.get("fuel_price")) : null,
      location: form.get("location") ? String(form.get("location")) : null,
    };

    try {
      const result = await api.createTrip(payload);
      setMessage(`Trip logged. MPG: ${result.mpg}`);
      event.currentTarget.reset();
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log trip");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">Log trip</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <input className="input" name="driver_id" placeholder="Driver ID" required />
        <input className="input" name="truck_number" placeholder="Truck number" required />
        <input className="input" name="miles_driven" type="number" step="0.1" placeholder="Miles driven" required />
        <input className="input" name="fuel_used" type="number" step="0.1" placeholder="Fuel used (gal)" required />
        <input className="input" name="load_weight" type="number" step="0.1" placeholder="Load weight (lbs)" />
        <input className="input" name="hours_driven" type="number" step="0.1" placeholder="Hours driven" />
        <input className="input" name="fuel_price" type="number" step="0.01" placeholder="Fuel price / gal" />
        <input className="input" name="location" placeholder="Location" />
      </div>
      <div className="flex items-center gap-3">
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? "Saving..." : "Save trip"}
        </button>
        {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
      </div>
    </form>
  );
}