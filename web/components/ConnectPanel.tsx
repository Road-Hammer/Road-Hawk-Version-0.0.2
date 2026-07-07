"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearAuthSession, loadAuthUser, loadConnection, saveConnection } from "@/lib/api";
import type { ConnectionConfig, ConnectionMode } from "@/lib/connection";

const MODE_OPTIONS: Array<{
  value: ConnectionMode;
  title: string;
  description: string;
  defaultApiUrl: string;
}> = [
  {
    value: "standalone",
    title: "Standalone",
    description: "Run the API and dashboard on this machine. Best for a single driver laptop or shop PC.",
    defaultApiUrl: "http://127.0.0.1:8000",
  },
  {
    value: "server",
    title: "Fleet server",
    description:
      "This machine hosts the Road Hawk API for remote users. Bind with ROAD_HAWK_API_HOST=0.0.0.0 and enable auth.",
    defaultApiUrl: "http://127.0.0.1:8000",
  },
  {
    value: "remote",
    title: "Remote client",
    description: "Connect this dashboard to a fleet server over LAN or WAN and sign in as a remote user.",
    defaultApiUrl: "http://192.168.1.50:8000",
  },
];

export function ConnectPanel() {
  const router = useRouter();
  const initial = loadConnection();
  const [mode, setMode] = useState<ConnectionMode>(initial.mode);
  const [apiUrl, setApiUrl] = useState(initial.apiUrl);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [healthMode, setHealthMode] = useState<string | null>(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [signedInUser, setSignedInUser] = useState(loadAuthUser());

  useEffect(() => {
    const selected = MODE_OPTIONS.find((option) => option.value === mode);
    if (selected && mode !== "remote" && apiUrl === initial.apiUrl) {
      setApiUrl(selected.defaultApiUrl);
    }
  }, [mode, apiUrl, initial.apiUrl]);

  async function onSaveConnection(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("save");
    setMessage(null);
    setError(null);

    const config: ConnectionConfig = { mode, apiUrl };
    saveConnection(config);

    try {
      const health = await api.testConnection(config);
      setHealthMode(health.mode);
      setAuthRequired(health.auth_required);
      setMessage(
        `Connected to ${config.apiUrl} (${health.mode}). Auth ${
          health.auth_required ? "required" : "not required"
        }.`,
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connection test failed");
    } finally {
      setBusy(null);
    }
  }

  async function onLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("login");
    setMessage(null);
    setError(null);

    const config: ConnectionConfig = { mode, apiUrl };
    saveConnection(config);

    try {
      const session = await api.login(config.apiUrl, { username, password });
      setSignedInUser(session.user);
      setMessage(`Signed in as ${session.user.display_name} (${session.user.role}).`);
      setPassword("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(null);
    }
  }

  async function onLogout() {
    setBusy("logout");
    setMessage(null);
    setError(null);
    try {
      await api.logout();
      setSignedInUser(null);
      setMessage("Signed out.");
      router.refresh();
    } catch (err) {
      clearAuthSession();
      setSignedInUser(null);
      setError(err instanceof Error ? err.message : "Signed out locally.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-4 lg:grid-cols-3">
        {MODE_OPTIONS.map((option) => {
          const active = mode === option.value;
          return (
            <button
              key={option.value}
              type="button"
              className={`panel text-left transition ${
                active ? "border-road-amber/60 ring-1 ring-road-amber/30" : "hover:border-road-amber/30"
              }`}
              onClick={() => {
                setMode(option.value);
                setApiUrl(option.defaultApiUrl);
              }}
            >
              <h3 className="text-lg font-semibold text-white">{option.title}</h3>
              <p className="mt-2 text-sm text-road-muted">{option.description}</p>
            </button>
          );
        })}
      </section>

      <form onSubmit={onSaveConnection} className="panel space-y-4">
        <h3 className="text-lg font-semibold text-white">Connection settings</h3>
        <div>
          <label className="mb-2 block text-sm text-road-muted" htmlFor="api-url">
            API URL
          </label>
          <input
            id="api-url"
            className="input"
            value={apiUrl}
            onChange={(event) => setApiUrl(event.target.value)}
            placeholder="http://127.0.0.1:8000"
            required
          />
        </div>
        <button className="btn-primary" type="submit" disabled={busy !== null}>
          {busy === "save" ? "Testing..." : "Save and test connection"}
        </button>
        {healthMode ? (
          <p className="text-sm text-road-muted">
            Server reports mode <span className="text-white">{healthMode}</span>
            {authRequired ? " · remote login required" : " · open access"}
          </p>
        ) : null}
      </form>

      {mode === "server" ? (
        <section className="panel space-y-3 text-sm text-road-muted">
          <h3 className="text-lg font-semibold text-white">Fleet server setup</h3>
          <p>On this host, set environment variables before starting the API:</p>
          <pre className="overflow-x-auto rounded-lg border border-road-border bg-black/30 p-4 text-xs text-road-amber">
{`ROAD_HAWK_MODE=server
ROAD_HAWK_API_HOST=0.0.0.0
ROAD_HAWK_AUTH_REQUIRED=1
ROAD_HAWK_ADMIN_USER=admin
ROAD_HAWK_ADMIN_PASSWORD=your-secure-password
ROAD_HAWK_CORS_ORIGINS=http://localhost:3000,http://your-client:3000`}
          </pre>
          <p>Remote users then choose Remote client, enter this server&apos;s API URL, and sign in.</p>
        </section>
      ) : null}

      <section className="panel space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-white">Remote login</h3>
            <p className="mt-1 text-sm text-road-muted">
              Required when the server has <code>ROAD_HAWK_AUTH_REQUIRED=1</code>.
            </p>
          </div>
          {signedInUser ? (
            <div className="text-sm text-road-muted">
              Signed in as <span className="text-white">{signedInUser.display_name}</span> (
              {signedInUser.role})
            </div>
          ) : null}
        </div>

        {signedInUser ? (
          <button className="btn-secondary" type="button" onClick={onLogout} disabled={busy !== null}>
            {busy === "logout" ? "Signing out..." : "Sign out"}
          </button>
        ) : (
          <form onSubmit={onLogin} className="grid gap-4 md:grid-cols-2">
            <input
              className="input"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="Username"
              autoComplete="username"
              required
            />
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              autoComplete="current-password"
              required
            />
            <button className="btn-primary md:col-span-2" type="submit" disabled={busy !== null}>
              {busy === "login" ? "Signing in..." : "Sign in to server"}
            </button>
          </form>
        )}
      </section>

      {message ? <p className="text-sm text-emerald-400">{message}</p> : null}
      {error ? <p className="text-sm text-red-400">{error}</p> : null}
    </div>
  );
}