const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type Stats = {
  trip_count: number;
  total_miles: number;
  total_fuel: number;
  avg_mpg: number;
  total_fuel_cost: number;
  driver_count: number;
  truck_count: number;
  maintenance_count: number;
};

export type Driver = { driver_id: string; name: string };
export type Truck = {
  truck_number: string;
  vin: string | null;
  make: string | null;
  model: string | null;
  year: number | null;
};

export type Trip = {
  id: number;
  driver_id: string;
  truck_number: string;
  miles_driven: number;
  fuel_used: number;
  mpg: number;
  fuel_cost: number | null;
  location: string | null;
  logged_at: string;
};

export type FuelReportRow = {
  driver_id: string;
  trip_count: number;
  total_miles: number;
  total_fuel: number;
  avg_mpg: number;
};

export type MaintenanceRecord = {
  id: number;
  truck_number: string;
  service_date: string;
  details: string;
  cost: number | null;
  created_at: string;
};

export const api = {
  getStats: () => request<Stats>("/api/stats"),
  getDrivers: () => request<Driver[]>("/api/drivers"),
  createDriver: (body: Driver) =>
    request<Driver>("/api/drivers", { method: "POST", body: JSON.stringify(body) }),
  getTrucks: () => request<Truck[]>("/api/trucks"),
  createTruck: (body: Truck) =>
    request<Truck>("/api/trucks", { method: "POST", body: JSON.stringify(body) }),
  getTrips: (limit = 25) => request<Trip[]>(`/api/trips?limit=${limit}`),
  createTrip: (body: Record<string, unknown>) =>
    request<Trip>("/api/trips", { method: "POST", body: JSON.stringify(body) }),
  getFuelReport: (driverId?: string) =>
    request<FuelReportRow[]>(
      driverId ? `/api/fuel-report?driver_id=${encodeURIComponent(driverId)}` : "/api/fuel-report",
    ),
  getMaintenance: (limit = 25) =>
    request<MaintenanceRecord[]>(`/api/maintenance?limit=${limit}`),
  createMaintenance: (body: Record<string, unknown>) =>
    request<MaintenanceRecord>("/api/maintenance", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  exportTrips: () =>
    request<{ path: string; message: string }>("/api/export/trips", { method: "POST" }),
};