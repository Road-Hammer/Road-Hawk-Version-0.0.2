## Repository Status

**Classification:** ACTIVE-BUILD  
**Purpose:** Fleet and driver operations platform for owner-operators and small fleets.  
**Use in Lucy/STWL:** Yes — core trucking ops module.  
**License checked:** Original work.  
**Safe to run:** Yes — CLI + web dashboard with SQLite persistence.  
**Next action:** Coyote voice integration and cloud sync.

### Quick Start (CLI)

```bash
cd road-hawk
pip install -e .
road-hawk
```

Or without installing:

```bash
python -m road_hawk
```

### Web UI

Terminal 1 — API server:

```bash
pip install -e .
road-hawk-api
```

Terminal 2 — web dashboard:

```bash
cd web
npm install
npm run dev
```

If `node` is not recognized, run once from repo root:

```powershell
.\scripts\repair-node-path.ps1
```

Then open a new terminal, or use `.\web\dev.cmd` directly.

Open http://localhost:3000

Data is stored in `data/road_hawk.db`. Legacy alpha code is preserved in `archive/`.

---

Road Hawk — Operational Command Software Suite





By Road Hammer 









Overview





Road Hawk is a purpose-built operational command and data management software suite designed specifically for the trucking and logistics industry. Developed by industry veterans, Road Hawk bridges the gap between the realities of life on the road and the operational demands of modern fleet management.



Built by a trucker — for truckers.









Mission Statement





“To provide practical, real-world software solutions that empower Truckers', Lease Purchase, owner-operators, and small to medium fleet managers to take control of their operations, their data, and their future.”










Core Features (Current & Planned Development)





Driver Log Management

Trip & Fuel Tracking

Maintenance & Repair Logs

Fleet Inventory Management

Expense & Financial Tracking

Broker & Facility Ratings

Load Tracking & Delivery Audits

Driver Health & Wellness Logs

Cloud Sync & Backup Ready

API-Ready for Future Integrations

Modular Framework for Expansion










Current Status





Development Phase: Alpha Testing

This project is actively under development. Core functionality is being stabilized. Features and structure are subject to change as development progresses.









Project Structure



/docs          → Project documentation, roadmaps, planning notes  

/src           → Active source code (.py files)  

/data          → Example log files, datasets (optional)  

README.md      → This file  

.gitignore     → File exclusion rules  

LICENSE        → To be added (if/when public release)  











Usage





Private Repository — Internal Development Use Only

This repository is currently restricted to authorized developers and collaborators working directly on Road Hawk.









Roadmap





Phase 1 → Core Logging & Reporting

Phase 2 → Modularization & Error Handling

Phase 3 → Automation, Syncing, & Cloud Functions

Phase 4 → User Interface Improvements

Phase 5 → Private Beta Release









Contact





Road Hammer Driver Solutions  

NEPA, USA

“Old School Truckin' Values. Building new School Tools.”





📫 Contact: [office@thatdambbs.com](mailto:office@thatdambbs.com)  

🔒 Security bugs? Check [SECURITY.md](./SECURITY.md)




Disclaimer


This is a private development repository for internal use only. Unauthorized access, distribution, or use is prohibited.




