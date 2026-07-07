# Road Hawk Version 0.0.2

**STWL** · Susquehanna Timberwolf Lines LLC  
**Product:** Road Hawk · **Brand:** Road Hammer

## Status

Road Hawk is back in current development.

This repository is the active Road Hammer / STWL development lane for fleet and driver operations. The MVP includes a modular Python backend (CLI + FastAPI), SQLite persistence, and a Next.js web dashboard.

**Classification:** ACTIVE-BUILD  
**Safe to run:** Yes — CLI + web dashboard with SQLite persistence  
**Next action:** Coyote voice integration and cloud sync

## License status

No public license is currently selected for this repository.

The prior MIT license marker is being retired as part of the current-development refresh. Do not treat this repository as open source unless a future license file or release note explicitly says otherwise.

## Deployment modes

Road Hawk is designed to run **multi-platform** (Windows, Linux, macOS) in three configurations:

| Mode | What runs where | Use case |
|---|---|---|
| **Standalone local** | CLI or API + SQLite + web UI on one machine | Driver laptop, shop PC, Lucy/Windows dev |
| **Standalone server** | API + SQLite on a host (`0.0.0.0`); clients connect over LAN/WAN | Fleet server, garage NUC, VPS |
| **Client (remote API)** | Web dashboard (or future API-aware clients) pointed at your server | Tablet/phone/laptop hitting a central Road Hawk server |

**Standalone server** (accept remote clients):

```bash
export ROAD_HAWK_API_HOST=0.0.0.0
export ROAD_HAWK_CORS_ORIGINS=http://localhost:3000,http://192.168.1.10:3000
pip install -e .
road-hawk-api
```

**Client dashboard** (hook to remote server of your choice):

```bash
# web/.env.local
NEXT_PUBLIC_API_URL=http://your-server:8000
```

Copy `.env.example` and `web/.env.example` for all options. Override data location with `ROAD_HAWK_DATA_DIR` for portable/per-device storage.

### Platform notes

- **npm scripts** default to cross-platform `next` commands (`npm run dev`).
- **Windows helpers**: `npm run dev:win` uses `bin\run-with-node.cmd` when Node is not on PATH.
- **Unix helpers**: `npm run dev:unix` or `scripts/start-api.sh` / `scripts/start-web.sh`.
- **`scripts/*.ps1`** are Windows-first convenience wrappers; shell scripts are the portable path.

## Quick Start (CLI)

```bash
pip install -e .
road-hawk
```

Or without installing:

```bash
python -m road_hawk
```

## Web UI

Terminal 1 — API server:

```bash
pip install -e .
road-hawk-api
```

Terminal 2 — web dashboard:

```powershell
.\scripts\setup-local.ps1   # first time only
.\scripts\start-web.ps1
```

Or manually:

```bash
cd web
npm install
npm run dev
```

If `node` is not recognized, run once from repo root:

```powershell
.\scripts\repair-node-path.ps1
```

Open http://localhost:3000 (API at http://127.0.0.1:8000)

Data is stored in `data/road_hawk.db`. Legacy code is preserved in `archive/` (including `archive/legacy-0.0.2/`).

## STWL brand assets

Canonical brand files live on **D:** at `D:\STWL\STWL\SCREENSHOTS\`. The web UI uses the STWL square logo synced into `web/public/brand/`.

```powershell
.\scripts\sync-brand-assets.ps1
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Smoke tests live in `tests/test_*.py` and are auto-discovered by pytest.

**CI on push to `Road-Hawk`:**
- `test` — `pytest -q`
- `web-build` — `npm ci` + `npm run build` in `web/`

## Project Structure

```
src/road_hawk/   → Python package (CLI, API, services, database, config)
web/             → Next.js dashboard
scripts/         → Start/setup helpers (.ps1 Windows, .sh cross-platform)
tests/           → pytest suite (test_services, test_api)
archive/         → Legacy prototypes and prior monolithic sources
data/            → SQLite database (gitignored)
.env.example     → Standalone/server/client environment template
```

## Contact

Susquehanna Timberwolf Lines LLC (STWL)  
Road Hammer Driver Solutions — NEPA, USA

"Old School Truckin' Values. Building new School Tools."

📫 [office@thatdambbs.com](mailto:office@thatdambbs.com)

## Copyright

© 2026 Susquehanna Timberwolf Lines LLC. All rights reserved.

Road Hawk is a Road Hammer product developed for STWL operations.