# Cancer 360 — NHS FDP Proof of Concept

A full-stack proof-of-concept implementation of the NHS Federated Data Platform Cancer 360 product, featuring realistic integration with hospital source systems (ICE pathology, RIS radiology, Somerset Cancer Register, ChemoCare SACT, MOSAIQ radiotherapy, Infoflex MDT) via the NHS Canonical Data Model.

## Architecture

```
Hospital Source Systems
  │
  ├── ICE / WinPath (HL7 v2.4 MLLP)  ──┐
  ├── RIS / PACS   (HL7 v2.4 MLLP)     │
  ├── Somerset CWT (XML / SFTP)         ├──→  Integration Engine  ──→  CDM (PostgreSQL)  ──→  Cancer 360 App
  ├── SACT / RTDS  (CSV / SFTP)         │         (Python)              (20+ tables)        (FastAPI + React)
  ├── PAS / CDS    (CSV extract)        │
  ├── MDT Infoflex (JSON API)          ──┘
  └── e-RS         (JSON API)
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL running on `localhost:5432` with credentials matching `backend/app/config.py`
- Node.js 20+ (optional, for frontend development)

### 1. Create and activate a virtual environment

```powershell
C:\Users\MS234\.conda\envs\llm_v1\python.exe -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install backend dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 3. Start the backend API

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 4. Seed with synthetic data (optional)

```powershell
.\.venv\Scripts\python.exe scripts\seed_database.py
```

### 5. Run the integration engine (optional)

```powershell
cd integration_engine
..\.venv\Scripts\python.exe replay.py
```

## Native Integration Simulation

The repo now includes a native Windows-friendly simulation flow under [source_systems](/c:/Users/MS234/Desktop/cancer360/source_systems) and [tie](/c:/Users/MS234/Desktop/cancer360/tie). It does not require Docker or Git.

### Generate journeys

```powershell
.\.venv\Scripts\python.exe source_systems\scenario_engine.py --patients 50 --output data\scenarios\journeys.json
```

### Generate source payloads

```powershell
.\.venv\Scripts\python.exe source_systems\run_all.py --scenarios data\scenarios\journeys.json --output-dir data
```

This creates:
- HL7 payloads for PAS, ICE, RIS, and Aria under `data\hl7\`
- CSV extracts for Somerset, Aria, and Endoscopy under `data\csv\`
- `data\manifest.json` for deterministic replay

### Replay directly into PostgreSQL

```powershell
.\.venv\Scripts\python.exe -m tie replay --data-dir data
```

### Run the live TIE

```powershell
.\.venv\Scripts\python.exe -m tie
```

Then in another terminal:

```powershell
.\.venv\Scripts\python.exe source_systems\run_all.py --scenarios data\scenarios\journeys.json --output-dir data --mode replay --mllp-host 127.0.0.1 --mllp-port 2575 --file-drop-dir incoming
```

### Useful simulation API routes

- `GET /api/v1/integration/status` for audit/DLQ/source-system health
- `GET /api/v1/patients/{nhs_number}/navigation` for Somerset/endoscopy-derived navigation items
- `GET /api/v1/pathways/{pathway_id}/navigation` for pathway-scoped navigation items
- `GET /studio` for the built-in Integration Studio operator console
- `GET /studio/playback` for the step-through replay screen with pause and forward/back controls
- `POST /api/v1/simulation/runs` to trigger a synthetic replay from the app itself

## Mirth Replacement Design

If you want Mirth Connect to replace the Python `tie` layer completely, start with:

- [mirth/CHANNEL_BLUEPRINT.md](/c:/Users/MS234/Desktop/cancer360/mirth/CHANNEL_BLUEPRINT.md)
- [mirth/sql/upserts.sql](/c:/Users/MS234/Desktop/cancer360/mirth/sql/upserts.sql)
- [mirth/code_templates/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/code_templates/README.md)
- [mirth/channels/channel_manifest.json](/c:/Users/MS234/Desktop/cancer360/mirth/channels/channel_manifest.json)
- [mirth/channel_xml/README.md](/c:/Users/MS234/Desktop/cancer360/mirth/channel_xml/README.md)
- [mirth/DEPLOYMENT_CHECKLIST.md](/c:/Users/MS234/Desktop/cancer360/mirth/DEPLOYMENT_CHECKLIST.md)

## Project Structure

```
cancer360/
├── init.sql                    # CDM PostgreSQL schema (20+ tables)
├── backend/                    # FastAPI application
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── config.py           # Environment configuration
│       ├── database.py         # Async SQLAlchemy engine
│       ├── auth/               # JWT + RBAC
│       ├── models/             # SQLAlchemy ORM (all CDM entities)
│       ├── schemas/            # Pydantic request/response models
│       ├── api/v1/             # REST endpoints (PTL, patients, actions, dashboard)
│       └── services/           # Business logic (PTL queries, pathway calculations)
├── integration_engine/         # Message broker & ETL
│   ├── adapters/               # MLLP receiver, file watcher, REST API
│   ├── parsers/                # HL7 v2, SACT CSV, RTDS CSV, Somerset XML, CDS
│   ├── mappers/                # Source → CDM transformation (pathology, radiology, etc.)
│   ├── orchestrator.py         # Pipeline controller
│   └── replay.py               # Synthetic data replay engine
├── src/                        # Shared utilities
│   └── synth_utils.py          # NHS number gen, date helpers, clinical logic
├── scripts/
│   └── seed_database.py        # Direct CDM seeder for PoC
└── config/                     # Reference data and config files
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/ptl` | Cancer Patient Tracking List (filtered, paginated) |
| GET | `/api/v1/ptl/summary` | PTL aggregate statistics |
| GET | `/api/v1/patients/{nhs}` | Patient 360° view |
| GET | `/api/v1/patients/{nhs}/pathology` | Pathology results (ICE/WinPath) |
| GET | `/api/v1/patients/{nhs}/radiology` | Radiology reports (RIS/PACS) |
| GET | `/api/v1/patients/{nhs}/treatment` | SACT + Radiotherapy records |
| GET | `/api/v1/patients/{nhs}/mdt` | MDT discussion outcomes |
| GET | `/api/v1/actions` | Cancer actions inbox |
| POST | `/api/v1/actions` | Create action |
| PATCH | `/api/v1/actions/{id}` | Update action |
| GET | `/api/v1/dashboard/performance` | Dashboard metrics |
| GET | `/api/v1/search?q=` | Patient search |
| POST | `/api/v1/auth/token` | JWT authentication |

## Canonical Data Model

The CDM follows the NHS FDP ontology pattern with these core entities:

- **patient** — NHS number, demographics, GP registration
- **referral** — 2WW/USC referrals with CWT clock start
- **diagnosis** — ICD-10 coded cancer diagnosis
- **staging** — TNM classification, stage group, grade
- **cancer_pathway** — Derived entity tracking 28d/62d targets and breach risk
- **pathology_result** + **pathology_result_value** + **histopath_structured** — ICE/WinPath results
- **radiology_result** — RIS imaging reports
- **sact_course** + **sact_cycle** + **sact_drug** — Chemotherapy records
- **radiotherapy_course** + **radiotherapy_fraction** — RT treatment records
- **mdt_discussion** — Multi-disciplinary team outcomes
- **cancer_action** — Worklist items
- **episode** / **appointment** — PAS admissions and clinic bookings

## Integration Patterns

| Source System | Protocol | Message Format | CDM Target |
|--------------|----------|---------------|------------|
| ICE / WinPath | MLLP TCP:2575 | HL7 v2.4 ORU^R01 | pathology_result |
| RIS / PACS | MLLP TCP:2575 | HL7 v2.4 ORU^R01 | radiology_result |
| Somerset | SFTP file drop | COSD XML | referral, diagnosis, staging, pathway |
| SACT (ChemoCare) | SFTP file drop | National SACT CSV | sact_course, sact_cycle |
| RTDS (MOSAIQ) | SFTP file drop | National RTDS CSV | radiotherapy_course |
| PAS (CDS) | SFTP file drop | CDS v6.3 CSV | episode, appointment |
| MDT (Infoflex) | REST API | JSON | mdt_discussion |
| e-RS | REST API | JSON | referral, appointment |

