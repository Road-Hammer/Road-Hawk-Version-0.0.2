# Road Hawk Version 0.0.2

## Status

Road Hawk is back in current development.

This repository is the active Road Hammer / STWL development lane for fleet and driver operations. The MVP includes a modular Python backend (CLI + FastAPI), SQLite persistence, and a Next.js web dashboard.

**Classification:** ACTIVE-BUILD  
**Safe to run:** Yes — CLI + web dashboard with SQLite persistence  
**Next action:** Coyote voice integration and cloud sync

## License status

No public license is currently selected for this repository.

The prior MIT license marker is being retired as part of the current-development refresh. Do not treat this repository as open source unless a future license file or release note explicitly says otherwise.

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

## Project Structure

```
src/road_hawk/   → Python package (CLI, API, services, database)
web/             → Next.js dashboard
scripts/         → Local dev helpers (start-api, start-web, setup)
tests/           → Python unit tests
archive/         → Legacy prototypes and prior monolithic sources
data/            → SQLite database (gitignored)
```

## Contact

Road Hammer Driver Solutions — NEPA, USA

"Old School Truckin' Values. Building new School Tools."

📫 [office@thatdambbs.com](mailto:office@thatdambbs.com)