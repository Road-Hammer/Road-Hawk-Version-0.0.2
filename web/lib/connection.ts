export type ConnectionMode = "standalone" | "server" | "remote";

export type ConnectionConfig = {
  mode: ConnectionMode;
  apiUrl: string;
};

export type AuthUser = {
  id: number;
  username: string;
  role: string;
  display_name: string;
};

export type AuthSession = {
  token: string;
  expires_at: string;
  user: AuthUser;
};

const CONNECTION_KEY = "road_hawk_connection";
const TOKEN_KEY = "road_hawk_token";
const USER_KEY = "road_hawk_user";
const DEFAULT_API = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export function defaultConnection(): ConnectionConfig {
  return {
    mode: "standalone",
    apiUrl: DEFAULT_API,
  };
}

export function normalizeApiUrl(raw: string): string {
  return raw.trim().replace(/\/+$/, "");
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function writeCookie(name: string, value: string, maxAgeSeconds: number) {
  if (typeof document === "undefined") {
    return;
  }
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax`;
}

export function loadConnection(): ConnectionConfig {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(CONNECTION_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as ConnectionConfig;
        if (parsed.apiUrl) {
          return { ...parsed, apiUrl: normalizeApiUrl(parsed.apiUrl) };
        }
      } catch {
        // fall through
      }
    }
  }

  const cookieUrl = readCookie("rh_api_url");
  const cookieMode = readCookie("rh_mode") as ConnectionMode | null;
  if (cookieUrl) {
    return {
      mode: cookieMode ?? "standalone",
      apiUrl: normalizeApiUrl(cookieUrl),
    };
  }

  return defaultConnection();
}

export function saveConnection(config: ConnectionConfig) {
  const normalized = {
    ...config,
    apiUrl: normalizeApiUrl(config.apiUrl),
  };
  if (typeof window !== "undefined") {
    localStorage.setItem(CONNECTION_KEY, JSON.stringify(normalized));
  }
  writeCookie("rh_mode", normalized.mode, 60 * 60 * 24 * 365);
  writeCookie("rh_api_url", normalized.apiUrl, 60 * 60 * 24 * 365);
}

export function loadAuthToken(): string | null {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      return token;
    }
  }
  return readCookie("rh_token");
}

export function loadAuthUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function saveAuthSession(session: AuthSession) {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, session.token);
    localStorage.setItem(USER_KEY, JSON.stringify(session.user));
  }
  writeCookie("rh_token", session.token, 60 * 60 * 12);
}

export function clearAuthSession() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
  writeCookie("rh_token", "", 0);
}

export async function resolveApiBase(): Promise<string> {
  if (typeof window === "undefined") {
    const { cookies } = await import("next/headers");
    const cookieStore = await cookies();
    const apiUrl = cookieStore.get("rh_api_url")?.value;
    if (apiUrl) {
      return normalizeApiUrl(apiUrl);
    }
    return DEFAULT_API;
  }
  return loadConnection().apiUrl;
}

export async function resolveAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") {
    const { cookies } = await import("next/headers");
    const cookieStore = await cookies();
    return cookieStore.get("rh_token")?.value ?? null;
  }
  return loadAuthToken();
}