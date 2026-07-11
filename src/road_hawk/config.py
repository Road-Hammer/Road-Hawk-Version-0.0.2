"""Runtime configuration for standalone and remote deployment modes."""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
_TRUE_VALUES = {"1", "true", "yes", "on"}
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def deploy_mode() -> str:
    """standalone = local API+DB on one machine; server = API host for remote clients; client = remote UI only."""
    raw = os.environ.get("ROAD_HAWK_MODE", "standalone").strip().lower()
    if raw in {"server", "standalone", "client"}:
        return raw
    return "standalone"


def connection_modes() -> list[str]:
    return ["standalone", "server", "client"]


def data_dir_override() -> Path | None:
    raw = os.environ.get("ROAD_HAWK_DATA_DIR", "").strip()
    return Path(raw) if raw else None


def api_host() -> str:
    return os.environ.get("ROAD_HAWK_API_HOST", DEFAULT_API_HOST).strip()


def is_loopback_host(host: str | None = None) -> bool:
    """Return True only for explicit local-loopback bind targets."""
    return (host or api_host()).strip().lower() in _LOOPBACK_HOSTS


def is_externally_exposed() -> bool:
    """Remote/server deployments must be treated as crossing a trust boundary."""
    return deploy_mode() == "server" or not is_loopback_host()


def api_reload() -> bool:
    """Development reload is opt-in and is never allowed on a non-loopback bind."""
    requested = os.environ.get("ROAD_HAWK_RELOAD", "").strip().lower() in _TRUE_VALUES
    return requested and is_loopback_host()


def api_port() -> int:
    return int(os.environ.get("ROAD_HAWK_API_PORT", str(DEFAULT_API_PORT)))


def api_url() -> str:
    explicit = os.environ.get("ROAD_HAWK_API_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = api_host()
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{api_port()}"


def cors_origins() -> list[str]:
    raw = os.environ.get("ROAD_HAWK_CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(DEFAULT_CORS_ORIGINS)


def apply_runtime_config() -> None:
    """Apply environment overrides before database access."""
    from . import database

    override = data_dir_override()
    if override is not None:
        database.set_data_root(override)
