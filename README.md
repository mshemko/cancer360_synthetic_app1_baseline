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
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+ (for frontend development)

### 1. Start the database

```bash
docker compose up db -d
```

### 2. Seed with synthetic data

```bash
pip install sqlalchemy asyncpg
python scripts/seed_database.py
```

### 3. Start the backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Run the integration engine (optional)

```bash
cd integration_engine
pip install -r requirements.txt
python replay.py  # Replays synthetic HL7/CSV/XML through the pipeline
```

### Full Docker Compose

```bash
docker compose up --build
```

## Project Structure

```
cancer360/
├── docker-compose.yml          # Full stack orchestration
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
