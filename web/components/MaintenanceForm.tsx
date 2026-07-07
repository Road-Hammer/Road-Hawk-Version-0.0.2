"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export function MaintenanceForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await api.createMaintenance({
      truck_number: String(form.get("truck_number")),
      service_date: String(form.get("service_date")),
      details: String(form.get("details")),
      cost: form.get("cost") ? Number(form.get("cost")) : null,
    });
    setMessage("Maintenance record saved.");
    event.currentTarget.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">Log maintenance</h3>
      <div className="grid gap-4 md:grid-cols-2">
        <input className="input" name="truck_number" placeholder="Truck number" required />
        <input className="input" name="service_date" type="date" required />
        <input className="input md:col-span-2" name="details" placeholder="Service details" required />
        <input className="input" name="cost" type="number" step="0.01" placeholder="Cost" />
      </div>
      <button className="btn-primary" type="submit">
        Save maintenance
      </button>
      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
    </form>
  );
}