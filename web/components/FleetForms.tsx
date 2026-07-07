"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export function DriverForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await api.createDriver({
      driver_id: String(form.get("driver_id")),
      name: String(form.get("name")),
    });
    setMessage("Driver saved.");
    event.currentTarget.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">Register driver</h3>
      <input className="input" name="driver_id" placeholder="Driver ID" required />
      <input className="input" name="name" placeholder="Driver name" required />
      <button className="btn-primary" type="submit">
        Save driver
      </button>
      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
    </form>
  );
}

export function TruckForm() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await api.createTruck({
      truck_number: String(form.get("truck_number")),
      vin: form.get("vin") ? String(form.get("vin")) : null,
      make: form.get("make") ? String(form.get("make")) : null,
      model: form.get("model") ? String(form.get("model")) : null,
      year: form.get("year") ? Number(form.get("year")) : null,
    });
    setMessage("Truck saved.");
    event.currentTarget.reset();
    router.refresh();
  }

  return (
    <form onSubmit={onSubmit} className="panel space-y-4">
      <h3 className="text-lg font-semibold text-white">Register truck</h3>
      <input className="input" name="truck_number" placeholder="Truck number" required />
      <input className="input" name="vin" placeholder="VIN" />
      <div className="grid gap-4 md:grid-cols-3">
        <input className="input" name="make" placeholder="Make" />
        <input className="input" name="model" placeholder="Model" />
        <input className="input" name="year" type="number" placeholder="Year" />
      </div>
      <button className="btn-primary" type="submit">
        Save truck
      </button>
      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
    </form>
  );
}