import {
  clearAuthSession,
  loadAuthUser,
  loadConnection,
  normalizeApiUrl,
  resolveApiBase,
  resolveAuthToken,
  saveAuthSession,
  saveConnection,
  type AuthSession,
  type AuthUser,
  type ConnectionConfig,
} from "@/lib/connection";

export type ConnectionInfo = {
  mode: string;
  connection_modes: string[];
  api_url: string;
  api_host: string;
  api_port: number;
  auth_required: boolean;
  roles: string[];
  server_hint: string;
  client_hint: string;
};

export type AuthStatus = {
  auth_required: boolean;
  authenticated: boolean;
  user: AuthUser | null;
  roles: string[];
};

function formatApiError(status: number, detail: string): string {
  const trimmed = detail.trim();
  if (!trimmed) {
    return `Request failed: ${status}`;
  }
  try {
    const parsed = JSON.parse(trimmed) as { detail?: string | Array<{ msg?: string }> };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (Array.isArray(parsed.detail)) {
      return parsed.detail.map((item) => item.msg ?? JSON.stringify(item)).join("; ");
    }
  } catch {
    // use raw body
  }
  return trimmed;
}

async function buildHeaders(extra?: HeadersInit): Promise<HeadersInit> {
  const token = await resolveAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(extra ?? {}),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const apiBase = await resolveApiBase();
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: await buildHeaders(init?.headers),
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(formatApiError(response.status, detail));
  }

  if (response.status === 204) {
    return undefined as T;
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

export type DocumentSummary = {
  id: number;
  document_type: string;
  original_filename: string;
  mime_type: string | null;
  source_type: string;
  extraction_method: string;
  verification_status: string;
  driver_id: string | null;
  truck_number: string | null;
  load_number: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentField = {
  id: number;
  document_id: number;
  field_name: string;
  extracted_value: string | null;
  corrected_value: string | null;
  confidence: number | null;
  verified: number;
  created_at: string;
  updated_at: string;
};

export type DocumentDetail = {
  document: DocumentSummary & { stored_path: string };
  extraction: {
    id: number;
    document_id: number;
    raw_text: string;
    ocr_confidence: number | null;
    parser_version: string;
    extraction_notes: string | null;
    created_at: string;
  } | null;
  fields: DocumentField[];
};

async function uploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const apiBase = await resolveApiBase();
  const token = await resolveAuthToken();
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    body: formData,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(formatApiError(response.status, detail));
  }

  return response.json() as Promise<T>;
}

async function downloadRequest(path: string, filename: string, init?: RequestInit): Promise<void> {
  const apiBase = await resolveApiBase();
  const token = await resolveAuthToken();
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function publicRequest<T>(apiBase: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${normalizeApiUrl(apiBase)}${path}`, {
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

export const api = {
  getConnectionInfo: () => request<ConnectionInfo>("/api/connection"),
  getAuthStatus: () => request<AuthStatus>("/api/auth/status"),
  login: async (apiBase: string, body: { username: string; password: string }) => {
    const result = await publicRequest<AuthSession>(apiBase, "/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body),
    });
    saveAuthSession(result);
    return result;
  },
  logout: async () => {
    try {
      await request<{ message: string }>("/api/auth/logout", { method: "POST" });
    } finally {
      clearAuthSession();
    }
  },
  testConnection: async (config: ConnectionConfig) => {
    return publicRequest<{
      status: string;
      mode: string;
      api_url: string;
      auth_required: boolean;
      connection_modes: string[];
    }>(config.apiUrl, "/api/health");
  },
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
  exportTrips: () => downloadRequest("/api/export/trips", "trips_export.csv", { method: "POST" }),
  importTrips: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return uploadRequest<{
      filename: string;
      imported: number;
      skipped: number;
      errors: string[];
      message: string;
    }>("/api/import/trips", formData);
  },
  getDocuments: (limit = 50) => request<DocumentSummary[]>(`/api/documents?limit=${limit}`),
  getDocument: (documentId: number) => request<DocumentDetail>(`/api/documents/${documentId}`),
  uploadDocument: (formData: FormData) =>
    uploadRequest<DocumentDetail>("/api/documents/upload", formData),
  verifyDocument: (
    documentId: number,
    body: { corrected_fields: Record<string, string>; document_type?: string },
  ) =>
    request<DocumentDetail>(`/api/documents/${documentId}/verify`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  rejectDocument: (
    documentId: number,
    body: { reason?: string; rejected?: boolean },
  ) =>
    request<DocumentDetail>(`/api/documents/${documentId}/reject`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  reprocessDocument: (documentId: number, body: { document_type_hint?: string }) =>
    request<DocumentDetail>(`/api/documents/${documentId}/reprocess`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  exportDocuments: () =>
    downloadRequest("/api/export/documents", "documents_export.csv", { method: "POST" }),
  getCompPlansMeta: () =>
    request<{
      position_types: string[];
      pay_methods: string[];
      scenario_types: string[];
      disclaimer: string;
    }>("/api/comp-plans/meta"),
  getCompPlans: () =>
    request<
      Array<{
        id: number;
        company_name: string;
        position_type: string;
        pay_method: string;
        notes: string | null;
        base_result: {
          weekly_net: number;
          annual_net: number;
          net_per_dispatched_mile: number;
          net_per_hour: number;
          risk_level: string;
        } | null;
      }>
    >("/api/comp-plans"),
  createCompPlan: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/api/comp-plans", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteCompPlan: (planId: number) =>
    request<void>(`/api/comp-plans/${planId}`, { method: "DELETE" }),
  compareCompPlans: (ids: number[], scenario = "base") =>
    request<{
      scenario: string;
      disclaimer: string;
      results: Array<{
        rank: number;
        plan_id: number;
        company_name: string;
        position_type: string;
        pay_method: string;
        weekly_net: number;
        monthly_net: number;
        annual_net: number;
        net_per_dispatched_mile: number;
        net_per_hour: number;
        risk_level: string;
        flags: Array<{ level: string; message: string }>;
        notes: string | null;
        calculation_notes: string;
      }>;
    }>(`/api/comp-plans/compare/ranked?ids=${ids.join(",")}&scenario=${encodeURIComponent(scenario)}`),
  exportCompPlans: () =>
    downloadRequest("/api/comp-plans/export", "comp_plans_export.csv", { method: "POST" }),
  importCompPlans: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return uploadRequest<{ imported: number; errors: string[]; message: string }>(
      "/api/comp-plans/import",
      formData,
    );
  },
};

export { loadConnection, saveConnection, loadAuthUser, clearAuthSession };