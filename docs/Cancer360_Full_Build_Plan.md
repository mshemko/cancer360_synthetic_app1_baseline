# Cancer 360 — Full-Stack Build Plan

## Purpose

This document is the master implementation plan for making the Cancer 360 application fully functional end-to-end: from parameterised synthetic data generation, through integration engine processing, canonical data model population, API exposure, and frontend display.

The goal is a system where you can set parameters (volume, cancer sites, date ranges, scenario mix) and generate a complete, realistic synthetic cancer tracking dataset that flows through every layer and is fully visible in the UI.

---

## 1. Current State Summary

| Layer | Status | Key Technology |
|-------|--------|----------------|
| Frontend (Cancer 360 UI) | Exists — React app with PTL, Patient 360, dashboards | React, JavaScript |
| Backend API | Exists — FastAPI with endpoints for patients, PTL, results, MDT, treatment | Python, FastAPI, SQLAlchemy |
| PostgreSQL database | Exists — init.sql defines canonical tables | PostgreSQL |
| Integration engine | Exists — adapters, parsers, mappers, orchestrator, replay | Python |
| Source systems (synthetic) | Exists — scenario and payload generation | Python |
| TIE (local runtime) | Exists — lightweight replay/integration broker | Python |
| Mirth (optional) | Placeholder — channel templates and deployment design | Mirth Connect |
| Canonical data model | Partially complete — core entities present, several spec tables missing | SQL |

### What is missing or incomplete

1. **Database**: Several spec tables not yet created (IPT, tracking comments, MDT meetings/bookings/notes, endoscopy, cancer sites, hospital sites). No formal raw/staging/audit schemas.
2. **Synthetic data generator**: Not yet parameterised for volume, scenario mix, or date ranges. Not all spec domains have generators.
3. **Integration engine**: Not all source-to-canonical mappers exist for every spec domain. No formal raw/staging landing. No error/audit logging tables.
4. **Mirth**: Not wired into the live pipeline. Exists as a design-only layer.
5. **API**: Missing endpoints for MDT meetings, bookings, notes, tracking comments, endoscopy, reference data, IPT.
6. **Frontend**: Missing or incomplete screens for MDT schedule, tracking comments, endoscopy results, IPT view, and several Patient 360 detail tabs.

---

## 2. Target State

A single command (or small set of commands) that:

1. Accepts parameters: number of patients, cancer site distribution, date range, scenario types, volume of results/appointments/treatments per patient.
2. Generates synthetic source payloads (HL7, CSV, XML, JSON) for every source system in the spec.
3. Replays those payloads through the integration engine (or Mirth).
4. Lands data in raw → staging → canonical → app layers in PostgreSQL.
5. Exposes all canonical and app data through FastAPI endpoints.
6. Displays everything in the Cancer 360 React UI — PTL, Patient 360, MDT, results, treatment, comments, dashboards.

---

## 3. Architecture Layers (Target)

```
┌─────────────────────────────────────────────────┐
│  PARAMETER CONTROL PANEL                        │
│  (CLI or config file)                           │
│  patients: 500                                  │
│  cancer_sites: [Lung, Breast, Colorectal, ...]  │
│  date_range: 2024-01-01 to 2025-12-31           │
│  scenarios: [referral, diagnosis, treatment, ...]│
│  results_per_patient: 3-8                       │
│  appointments_per_patient: 2-6                  │
│  mdt_rate: 0.7                                  │
│  ipt_rate: 0.15                                 │
│  endoscopy_rate: 0.3                            │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  SYNTHETIC SOURCE SYSTEMS                       │
│  source_systems/                                │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ PAS/EPR  │ │ Somerset │ │ ICE/WinPath      ││
│  │ (CSV)    │ │ (XML)    │ │ (HL7)            ││
│  └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ RIS/PACS │ │ SACT/    │ │ Infoflex MDT     ││
│  │ (HL7)    │ │ ChemoCare│ │ (JSON)           ││
│  │          │ │ (CSV)    │ │                  ││
│  └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐                     │
│  │ Endoscopy│ │ e-RS     │                     │
│  │ (CSV/HL7)│ │ (JSON)   │                     │
│  └──────────┘ └──────────┘                     │
└──────────────────────┬──────────────────────────┘
                       │
          Payloads: HL7 / CSV / XML / JSON
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  INTEGRATION ENGINE                             │
│  integration_engine/                            │
│                                                 │
│  Adapters → Parsers → Mappers → Loaders         │
│                                                 │
│  Orchestrator controls pipeline per source       │
│  Replay engine re-processes historical batches   │
│  Error handler logs failures + retries           │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  POSTGRESQL (layered schemas)                   │
│                                                 │
│  raw.*          — original payloads             │
│  staging.*      — parsed source-shaped records  │
│  canonical.*    — standardised business entities│
│  ref.*          — reference/lookup tables       │
│  app.*          — presentation views            │
│  audit.*        — lineage, refresh, errors      │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  FASTAPI BACKEND                                │
│  backend/app/                                   │
│                                                 │
│  API v1 endpoints → Services → Repositories     │
│  Auth (JWT) → Role-based access                 │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│  CANCER 360 UI (React)                          │
│                                                 │
│  PTL list        │ Patient 360   │ Dashboards   │
│  MDT schedule    │ Results       │ Actions      │
│  Treatment       │ Comments      │ IPT          │
│  Endoscopy       │ Encounters    │ Reference    │
└─────────────────────────────────────────────────┘
```

---

## 4. Database Plan

### 4.1 Schema Structure

Create these schemas in PostgreSQL:

| Schema | Purpose |
|--------|---------|
| `raw` | Original source payloads for replay and audit |
| `staging` | Parsed source-shaped records before canonical mapping |
| `canonical` | Standardised business entities (the CDM) |
| `ref` | Reference and lookup tables |
| `app` | Presentation views and materialised views for the UI |
| `audit` | Load logs, refresh tracking, error records |

### 4.2 Raw Tables

| Table | Purpose |
|-------|---------|
| `raw.hl7_message` | HL7 v2 messages (pathology, radiology) |
| `raw.csv_extract` | CSV file rows (SACT, PAS demographics, endoscopy) |
| `raw.xml_payload` | XML documents (Somerset referrals) |
| `raw.json_payload` | JSON messages (MDT, e-RS) |

Common columns: `id`, `source_system`, `message_type`, `payload_text`, `file_name`, `received_at`, `correlation_id`, `processing_status`, `error_message`.

### 4.3 Staging Tables

| Table | Source System |
|-------|--------------|
| `staging.pas_patient` | PAS/EPR CSV |
| `staging.somerset_pathway` | Somerset XML |
| `staging.pathology_hl7` | ICE/WinPath HL7 |
| `staging.radiology_hl7` | RIS/PACS HL7 |
| `staging.sact_treatment` | SACT/ChemoCare CSV |
| `staging.mdt_source` | Infoflex JSON |
| `staging.endoscopy_source` | Endoscopy CSV/HL7 |
| `staging.eRS_referral` | e-RS JSON |

### 4.4 Canonical Tables (per NNUH V5 Spec)

Every table below includes `source_system_name` (VARCHAR) and `last_refreshed_at_source_timestamp` (TIMESTAMPTZ) as required by the spec.

#### patient

| Column | Type | Notes |
|--------|------|-------|
| person_id | VARCHAR PK | Unique patient identifier |
| mrn | VARCHAR | Hospital number |
| nhs_number | VARCHAR | National identifier |
| first_name | VARCHAR | |
| surname | VARCHAR | |
| title | VARCHAR | |
| date_of_birth | DATE | |
| date_of_death | DATE | Nullable |
| sex | VARCHAR | Phenotypic sex |
| gender_identity | VARCHAR | |
| address_line_1 | VARCHAR | |
| address_line_2 | VARCHAR | |
| postcode | VARCHAR | |
| phone_number | VARCHAR | |
| registered_gp | VARCHAR | |
| next_of_kin_name | VARCHAR | Optional |
| next_of_kin_number | VARCHAR | Optional |

Derived in views: `full_name`, `age`, `deceased`.

#### cancer_pathway

| Column | Type | Notes |
|--------|------|-------|
| pathway_id | VARCHAR PK | |
| person_id | VARCHAR FK→patient | |
| mrn | VARCHAR | |
| nhs_number | VARCHAR | |
| first_name | VARCHAR | |
| surname | VARCHAR | |
| full_name | VARCHAR | |
| original_pathway_start_date | DATE | |
| pathway_closed_date | DATE | Nullable |
| waiting_time_adjustment_days | INTEGER | Default 0 |
| adjusted_pathway_start_date | DATE | |
| cancer_site | VARCHAR | |
| cancer_sub_site | VARCHAR | |
| hospital_site | VARCHAR | |
| hospital_site_id | VARCHAR FK→hospital_sites | |
| pathway_status | VARCHAR | open/closed |
| pathway_referral_route | VARCHAR | |
| first_seen_site | VARCHAR | |
| first_seen_site_ods_code | VARCHAR | |
| 28_day_breach_date | DATE | Computed: start + 28 |
| 31_day_breach_date | DATE | |
| 62_day_breach_date | DATE | |
| patient_informed_date | DATE | |
| referral_received_date | DATE | |
| upgrade_date | DATE | |
| date_of_birth | DATE | For upgrade pathways |
| date_of_death | DATE | |
| decision_to_treat_date | DATE | |
| diagnosis | VARCHAR | |
| diagnosis_icd_10_code | VARCHAR | |
| diagnosis_date | DATE | |
| first_seen_date | DATE | |
| first_treatment_date | DATE | |
| first_treatment_type | VARCHAR | |
| organisation_site_treatment | VARCHAR | |
| treatment_site_ods_code | VARCHAR | |
| treatment_site | VARCHAR | |
| referral_source | VARCHAR | |
| is_benign | BOOLEAN | Derivable |
| is_62_day_pathway_open | BOOLEAN | Required |
| is_31_day_pathway_open | BOOLEAN | Required |
| is_28_day_pathway_open | BOOLEAN | Required |
| is_any_pathway_type_open | BOOLEAN | OR of above |

#### ipt

| Column | Type |
|--------|------|
| tertiary_id | VARCHAR PK |
| pathway_id | VARCHAR FK→cancer_pathway |
| person_id | VARCHAR FK→patient |
| nhs_number | VARCHAR |
| mrn | VARCHAR |
| tertiary_referral_type | VARCHAR |
| tertiary_reason | VARCHAR |
| tertiary_reason_code | VARCHAR |
| sending_org_id | VARCHAR |
| sending_org_name | VARCHAR |
| receiving_org_id | VARCHAR |
| receiving_org_name | VARCHAR |
| tertiary_sent_date | DATE |
| tertiary_received_date | DATE |
| tertiary_returned_date | DATE |
| tertiary_sending_comment | VARCHAR |
| tertiary_return_comment | VARCHAR |
| is_sent | BOOLEAN |
| is_received | BOOLEAN |
| is_returned | BOOLEAN |

#### tracking_comment

| Column | Type |
|--------|------|
| cancer_tracking_comment_id | VARCHAR PK |
| cancer_pathway_id | VARCHAR FK→cancer_pathway |
| comment_title | VARCHAR |
| comment_text | TEXT |
| created_by | VARCHAR |
| created_at_timestamp | TIMESTAMPTZ |

#### mdt_meeting

| Column | Type |
|--------|------|
| mdt_meeting_id | VARCHAR PK |
| meeting_timestamp | TIMESTAMPTZ |
| mdt_status | VARCHAR |

#### mdt_booking

| Column | Type |
|--------|------|
| meeting_id | VARCHAR FK→mdt_meeting (composite PK) |
| pathway_id | VARCHAR FK→cancer_pathway (composite PK) |

#### mdt_note

| Column | Type |
|--------|------|
| mdt_note_id | VARCHAR PK |
| cancer_pathway_id | VARCHAR FK→cancer_pathway |
| meeting_id | VARCHAR FK→mdt_meeting |
| note_type | VARCHAR |
| mdt_note_text | TEXT |
| last_updated_timestamp | TIMESTAMPTZ |

#### inpatient_encounter

| Column | Type |
|--------|------|
| encounter_id | VARCHAR PK |
| person_id | VARCHAR FK→patient |
| title | VARCHAR |
| tci_status | VARCHAR |
| surgical_order_date | DATE |
| admission_offer_timestamp | DATE |
| attendance_date | DATE |

#### outpatient_appointment

| Column | Type |
|--------|------|
| attendance_id | VARCHAR PK |
| person_id | VARCHAR FK→patient |
| type | VARCHAR |
| booking_status | VARCHAR |
| start_date_time | DATE |
| ordered_date | DATE |
| date_time_booked | DATE |

#### cancer_treatment

| Column | Type |
|--------|------|
| cancer_treatment_id | VARCHAR PK |
| person_id | VARCHAR FK→patient |
| treatment_type | VARCHAR |
| treatment_description | VARCHAR |
| treatment_status | VARCHAR |
| attendance_date | DATE |
| ordered_date | DATE |
| scheduled_date | DATE |
| poa_attendance_id | VARCHAR FK→outpatient_appointment |
| poa_booking_status | VARCHAR |
| prescription_status | VARCHAR |
| is_prescription_prepared | BOOLEAN |

#### endoscopy

| Column | Type |
|--------|------|
| endoscopy_id | VARCHAR PK |
| person_id | VARCHAR FK→patient |
| endoscopy_type | VARCHAR |
| modality | VARCHAR |
| endoscopy_priority | VARCHAR |
| exam_status | VARCHAR |
| ordered_date | DATE |
| scheduled_date | DATE |
| attendance_date | DATE |
| report_prepared_date | DATE |
| report_authorised_date | DATE |
| is_reported | BOOLEAN |
| endoscopy_report_text | TEXT |

#### radiology

| Column | Type |
|--------|------|
| radiology_exam_id | VARCHAR PK |
| patient_id | VARCHAR FK→patient |
| radiology_exam_type | VARCHAR |
| modality | VARCHAR |
| radiology_priority | VARCHAR |
| exam_status | VARCHAR |
| ordered_date | DATE |
| scheduled_date | DATE |
| attendance_date | DATE |
| report_authorised_date | DATE |
| is_reported | BOOLEAN |
| radiology_report_text | TEXT |

#### histology

| Column | Type |
|--------|------|
| histology_id | VARCHAR PK (add this) |
| person_id | VARCHAR FK→patient |
| histology_type | VARCHAR |
| priority | VARCHAR |
| histology_status | VARCHAR |
| sample_taken_date | DATE |
| received_at_lab_date | DATE |
| sample_prepared_date | DATE |
| report_prepared_date | DATE |
| report_authorised_date | DATE |
| is_reported | BOOLEAN |
| histology_report_text | TEXT |

#### test_result

| Column | Type |
|--------|------|
| test_result_id | VARCHAR PK |
| person_id | VARCHAR FK→patient |
| attendance_id | VARCHAR FK→outpatient_appointment |
| test_name | VARCHAR |
| test_id_code | VARCHAR |
| test_date_time | TIMESTAMPTZ |
| test_ordered_timestamp | TIMESTAMPTZ |
| value | VARCHAR |
| value_double | DOUBLE PRECISION |
| test_value_type | VARCHAR |
| unit | VARCHAR |
| ordering_specialty_name | VARCHAR |
| expiry_date | TIMESTAMPTZ |

### 4.5 Reference Tables

#### ref.cancer_site

| Column | Type |
|--------|------|
| cancer_site_id | VARCHAR PK |
| cancer_site | VARCHAR |
| cancer_subsite | VARCHAR[] (array) |

#### ref.hospital_site

| Column | Type |
|--------|------|
| hospital_site_id | VARCHAR PK |
| hospital_site | VARCHAR |

### 4.6 App Views

| View | Purpose | Key joins |
|------|---------|-----------|
| `app.vw_ptl` | Patient Tracking List — main operational view | cancer_pathway + patient + latest results + breach flags |
| `app.vw_patient_360` | Patient summary for detail screen | patient + pathways + latest of each domain |
| `app.vw_mdt_schedule` | MDT meetings with booked patients and notes | mdt_meeting + mdt_booking + cancer_pathway + mdt_note |
| `app.vw_results` | Unified results view across radiology, histology, test results | UNION of radiology + histology + test_result |
| `app.vw_treatment_timeline` | Treatment events with dates and statuses | cancer_treatment + outpatient_appointment |
| `app.vw_tracking_comments` | Comments per pathway | tracking_comment + cancer_pathway |
| `app.vw_endoscopy` | Endoscopy list with report status | endoscopy + patient |
| `app.vw_ipt` | Inter-provider transfers | ipt + cancer_pathway + patient |
| `app.vw_encounters` | Combined inpatient + outpatient encounters | UNION of inpatient_encounter + outpatient_appointment |

### 4.7 Audit Tables

| Table | Purpose |
|-------|---------|
| `audit.load_log` | Tracks each integration batch: source, start time, end time, rows loaded, status |
| `audit.error_log` | Failed records: source, payload snippet, error message, timestamp |
| `audit.refresh_status` | Per-table last refresh timestamp (drives UI refresh indicators) |

---

## 5. Synthetic Data Generator Plan

### 5.1 Parameter Model

Create a configuration file (`config/generation_params.yaml` or `.json`):

```yaml
generation:
  patients: 500
  date_range:
    start: "2024-01-01"
    end: "2025-12-31"

  cancer_site_distribution:
    Lung: 0.20
    Breast: 0.20
    Colorectal: 0.18
    Prostate: 0.10
    Head & Neck: 0.08
    Upper GI: 0.08
    Haematology: 0.06
    Gynaecology: 0.05
    Skin: 0.03
    Urology: 0.02

  pathway_settings:
    open_rate: 0.60           # 60% of pathways are currently open
    benign_rate: 0.25         # 25% diagnosed benign
    upgrade_rate: 0.10        # 10% are upgrade pathways
    breach_28_rate: 0.12
    breach_62_rate: 0.08

  scenario_rates:
    has_diagnosis: 0.70
    has_first_treatment: 0.50
    has_mdt: 0.70
    has_ipt: 0.15
    has_endoscopy: 0.30
    has_radiology: 0.85
    has_histology: 0.75
    has_test_results: 0.90
    has_inpatient: 0.40
    has_outpatient: 0.95
    has_tracking_comments: 0.60

  volume_per_patient:
    radiology_exams: { min: 1, max: 5 }
    histology_samples: { min: 1, max: 3 }
    test_results: { min: 2, max: 10 }
    outpatient_appointments: { min: 1, max: 8 }
    inpatient_encounters: { min: 0, max: 3 }
    cancer_treatments: { min: 0, max: 6 }
    endoscopy_exams: { min: 0, max: 2 }
    tracking_comments: { min: 0, max: 5 }
    mdt_meetings_per_site: { min: 4, max: 12 }
    mdt_notes_per_pathway: { min: 0, max: 3 }
    ipt_per_pathway: { min: 0, max: 2 }

  hospital_sites:
    - { id: "NNUH", name: "Norfolk and Norwich University Hospital" }
    - { id: "JPH", name: "James Paget Hospital" }
    - { id: "QEH", name: "Queen Elizabeth Hospital" }

  source_systems:
    patient: "PAS"
    pathway: "Somerset"
    pathology: "ICE"
    radiology: "CRIS"
    treatment: "ChemoCare"
    mdt: "Infoflex"
    endoscopy: "Unisoft"
    appointments: "PAS"
    encounters: "PAS"
```

### 5.2 Generator Architecture

```
source_systems/
  config/
    generation_params.yaml       ← parameters above
    reference_data/
      cancer_sites.json          ← site/subsite seed
      hospital_sites.json        ← hospital seed
      icd10_codes.json           ← diagnosis code seed
      test_names.json            ← pathology test names
      radiology_types.json       ← exam types + modalities
      histology_types.json
      endoscopy_types.json
      treatment_regimens.json    ← chemo/radio regimen names
      hl7_templates/             ← HL7 message templates
      xml_templates/             ← Somerset XML templates
  generators/
    orchestrator.py              ← master controller
    patient_generator.py         ← demographics
    pathway_generator.py         ← cancer pathways + dates
    referral_generator.py        ← referral details
    diagnosis_generator.py       ← diagnosis + staging
    radiology_generator.py       ← radiology exams
    histology_generator.py       ← histology samples
    test_result_generator.py     ← blood/pathology tests
    treatment_generator.py       ← SACT / radiotherapy
    mdt_generator.py             ← meetings + bookings + notes
    appointment_generator.py     ← OP appointments
    encounter_generator.py       ← inpatient encounters
    endoscopy_generator.py       ← endoscopy exams
    ipt_generator.py             ← inter-provider transfers
    comment_generator.py         ← tracking comments
  renderers/
    hl7_renderer.py              ← render to HL7 v2 messages
    csv_renderer.py              ← render to CSV extracts
    xml_renderer.py              ← render to Somerset XML
    json_renderer.py             ← render to JSON payloads
  output/
    hl7/                         ← generated HL7 files
    csv/                         ← generated CSV files
    xml/                         ← generated XML files
    json/                        ← generated JSON files
    journeys/                    ← master journey records (JSON)
  run_generation.py              ← CLI entry point
```

### 5.3 Generation Flow

```
run_generation.py --config config/generation_params.yaml
  │
  ├─ 1. Load params + reference data
  ├─ 2. Generate N patients (patient_generator)
  ├─ 3. For each patient, generate pathways (pathway_generator)
  │     └─ Apply cancer_site_distribution, open/closed rates
  ├─ 4. For each pathway, generate clinical events:
  │     ├─ diagnosis (if scenario applies)
  │     ├─ radiology exams (volume range)
  │     ├─ histology samples (volume range)
  │     ├─ test results (volume range)
  │     ├─ OP appointments (volume range)
  │     ├─ inpatient encounters (volume range)
  │     ├─ cancer treatments (volume range)
  │     ├─ endoscopy exams (if scenario applies)
  │     ├─ MDT booking (if scenario applies)
  │     ├─ MDT notes (if scenario applies)
  │     ├─ IPT (if scenario applies)
  │     └─ tracking comments (volume range)
  ├─ 5. Save master journey records to output/journeys/
  ├─ 6. Render source payloads:
  │     ├─ Patient demographics → CSV (PAS extract)
  │     ├─ Pathways → XML (Somerset) + CSV
  │     ├─ Pathology/histology → HL7 ORU (ICE/WinPath)
  │     ├─ Radiology → HL7 ORU (RIS/CRIS)
  │     ├─ Treatment → CSV (SACT/ChemoCare)
  │     ├─ MDT → JSON (Infoflex)
  │     ├─ Endoscopy → CSV (Unisoft)
  │     ├─ Appointments/encounters → CSV (PAS)
  │     ├─ IPT → CSV (Somerset/cancer register)
  │     └─ Tracking comments → CSV (cancer register)
  └─ 7. Write files to output/ directories
```

### 5.4 Key Design Decisions for the Generator

1. **Temporal coherence**: All dates within a patient journey must be logically ordered (referral → first seen → diagnosis → MDT → treatment). The pathway generator creates a timeline skeleton that downstream generators respect.

2. **Identity consistency**: Each patient gets one person_id, one mrn, one nhs_number used across all source payloads. The patient_generator creates the master identity record.

3. **Realistic distributions**: Use configurable rates for breach, benign, upgrade, and scenario inclusion. Use weighted random for cancer site allocation.

4. **Referential integrity**: Every FK relationship in the spec (person_id, pathway_id, meeting_id, attendance_id) must be consistent across generated records.

5. **Source format fidelity**: HL7 messages should include realistic segments (MSH, PID, PV1, OBR, OBX). CSV files should match the column structure expected by parsers. Somerset XML should follow known template structure.

---

## 6. Integration Engine Plan

### 6.1 Architecture

```
integration_engine/
  adapters/
    file_watcher.py          ← watch output/ directories for new files
    hl7_receiver.py          ← receive HL7 messages (MLLP or file)
    csv_reader.py            ← read CSV extracts
    xml_reader.py            ← read XML documents
    json_reader.py           ← read JSON payloads
  parsers/
    hl7_parser.py            ← parse HL7 v2 segments into dicts
    csv_parser.py            ← parse CSV rows
    xml_parser.py            ← parse Somerset XML
    json_parser.py           ← parse JSON structures
  mappers/
    patient_mapper.py        ← PAS → canonical.patient
    pathway_mapper.py        ← Somerset → canonical.cancer_pathway
    radiology_mapper.py      ← RIS HL7 → canonical.radiology
    histology_mapper.py      ← ICE HL7 → canonical.histology
    test_result_mapper.py    ← ICE HL7 → canonical.test_result
    treatment_mapper.py      ← SACT CSV → canonical.cancer_treatment
    mdt_mapper.py            ← Infoflex JSON → canonical.mdt_meeting + mdt_booking + mdt_note
    endoscopy_mapper.py      ← Unisoft CSV → canonical.endoscopy
    appointment_mapper.py    ← PAS CSV → canonical.outpatient_appointment
    encounter_mapper.py      ← PAS CSV → canonical.inpatient_encounter
    ipt_mapper.py            ← Somerset/register → canonical.ipt
    comment_mapper.py        ← Register CSV → canonical.tracking_comment
    reference_mapper.py      ← Seeds → ref.cancer_site + ref.hospital_site
  loaders/
    raw_loader.py            ← insert into raw.* tables
    staging_loader.py        ← insert into staging.* tables
    canonical_loader.py      ← upsert into canonical.* tables
    reference_loader.py      ← seed/upsert ref.* tables
    audit_logger.py          ← write to audit.* tables
  orchestrator.py            ← controls pipeline: raw → staging → canonical → audit
  replay.py                  ← re-process from raw or from file
  error_handler.py           ← catch, log, retry logic
  config.py                  ← DB connection, paths, settings
```

### 6.2 Pipeline Flow (per source)

```
File arrives in output/{format}/
  │
  ├─ 1. Adapter detects file, reads content
  ├─ 2. Raw loader stores original payload in raw.*
  ├─ 3. Parser converts payload into structured dict
  ├─ 4. Staging loader stores parsed records in staging.*
  ├─ 5. Mapper transforms staged records into canonical shape
  ├─ 6. Canonical loader upserts into canonical.*
  ├─ 7. Audit logger records: source, file, rows, status, timestamp
  └─ 8. Error handler catches failures, logs to audit.error_log
```

### 6.3 Source-to-Canonical Mapping Summary

| Source System | Format | Adapter | Parser | Mapper | Canonical Target |
|---------------|--------|---------|--------|--------|-----------------|
| PAS/EPR | CSV | csv_reader | csv_parser | patient_mapper | patient |
| Somerset | XML | xml_reader | xml_parser | pathway_mapper | cancer_pathway |
| ICE/WinPath | HL7 | hl7_receiver | hl7_parser | histology_mapper | histology |
| ICE/WinPath | HL7 | hl7_receiver | hl7_parser | test_result_mapper | test_result |
| RIS/CRIS | HL7 | hl7_receiver | hl7_parser | radiology_mapper | radiology |
| SACT/ChemoCare | CSV | csv_reader | csv_parser | treatment_mapper | cancer_treatment |
| Infoflex | JSON | json_reader | json_parser | mdt_mapper | mdt_meeting + mdt_booking + mdt_note |
| Unisoft | CSV | csv_reader | csv_parser | endoscopy_mapper | endoscopy |
| PAS/EPR | CSV | csv_reader | csv_parser | appointment_mapper | outpatient_appointment |
| PAS/EPR | CSV | csv_reader | csv_parser | encounter_mapper | inpatient_encounter |
| Somerset/Register | CSV | csv_reader | csv_parser | ipt_mapper | ipt |
| Cancer Register | CSV | csv_reader | csv_parser | comment_mapper | tracking_comment |
| Reference seed | JSON | json_reader | json_parser | reference_mapper | ref.cancer_site + ref.hospital_site |

---

## 7. Mirth Connect Plan

### 7.1 Role

Mirth sits as an optional enterprise-grade replacement for the Python integration engine. For this build, Mirth should be wired in parallel so you can demonstrate both approaches.

### 7.2 Channel Design

| Channel | Source | Destination | Transform |
|---------|--------|-------------|-----------|
| PAS Patient Ingest | CSV file reader | PostgreSQL canonical.patient | CSV → patient mapping |
| Somerset Pathway Ingest | XML file reader | PostgreSQL canonical.cancer_pathway | XML → pathway mapping |
| Pathology HL7 Ingest | HL7 MLLP listener or file | PostgreSQL canonical.histology + test_result | HL7 ORU → histology/test mapping |
| Radiology HL7 Ingest | HL7 MLLP listener or file | PostgreSQL canonical.radiology | HL7 ORU → radiology mapping |
| SACT Treatment Ingest | CSV file reader | PostgreSQL canonical.cancer_treatment | CSV → treatment mapping |
| MDT JSON Ingest | JSON file reader | PostgreSQL canonical.mdt_* | JSON → mdt mapping |
| Endoscopy Ingest | CSV file reader | PostgreSQL canonical.endoscopy | CSV → endoscopy mapping |
| Appointment Ingest | CSV file reader | PostgreSQL canonical.outpatient_appointment | CSV → appointment mapping |
| Encounter Ingest | CSV file reader | PostgreSQL canonical.inpatient_encounter | CSV → encounter mapping |
| IPT Ingest | CSV file reader | PostgreSQL canonical.ipt | CSV → ipt mapping |
| Comment Ingest | CSV file reader | PostgreSQL canonical.tracking_comment | CSV → comment mapping |

### 7.3 Mirth Deployment on Windows Server

- Install Mirth Connect as a Windows service.
- Configure channels to watch the same output directories used by the synthetic generator.
- Each channel writes to the same canonical PostgreSQL schema.
- Add a global channel for audit logging.

---

## 8. API Plan

### 8.1 Endpoint Catalogue (Target)

#### Patient
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/patients/{person_id}` | canonical.patient + app.vw_patient_360 |
| GET | `/api/v1/patients/{person_id}/pathways` | canonical.cancer_pathway |
| GET | `/api/v1/patients/{person_id}/radiology` | canonical.radiology |
| GET | `/api/v1/patients/{person_id}/histology` | canonical.histology |
| GET | `/api/v1/patients/{person_id}/test-results` | canonical.test_result |
| GET | `/api/v1/patients/{person_id}/treatment` | canonical.cancer_treatment |
| GET | `/api/v1/patients/{person_id}/endoscopy` | canonical.endoscopy |
| GET | `/api/v1/patients/{person_id}/encounters` | app.vw_encounters |
| GET | `/api/v1/patients/{person_id}/mdt` | mdt_booking + mdt_note (joined) |
| GET | `/api/v1/patients/{person_id}/comments` | canonical.tracking_comment |
| GET | `/api/v1/patients/{person_id}/ipt` | canonical.ipt |
| GET | `/api/v1/patients/{person_id}/timeline` | Aggregated chronological events |

#### PTL
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/ptl` | app.vw_ptl |
| GET | `/api/v1/ptl/summary` | Aggregation on vw_ptl |
| GET | `/api/v1/ptl/filters` | ref.cancer_site + ref.hospital_site |

#### MDT
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/mdt/meetings` | canonical.mdt_meeting |
| GET | `/api/v1/mdt/meetings/{meeting_id}` | mdt_meeting + mdt_booking + mdt_note |
| GET | `/api/v1/mdt/bookings` | canonical.mdt_booking |
| GET | `/api/v1/mdt/notes` | canonical.mdt_note |

#### Treatment
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/treatments` | canonical.cancer_treatment |
| GET | `/api/v1/treatments/{person_id}` | canonical.cancer_treatment filtered |

#### Comments / Actions
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/comments` | canonical.tracking_comment |
| POST | `/api/v1/comments` | Insert to canonical.tracking_comment |
| GET | `/api/v1/actions` | Existing action table |

#### Reference
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/reference/cancer-sites` | ref.cancer_site |
| GET | `/api/v1/reference/hospital-sites` | ref.hospital_site |

#### Search
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/search?q=` | canonical.patient (name, nhs, mrn) |

#### Dashboard
| Method | Path | Source |
|--------|------|--------|
| GET | `/api/v1/dashboard/performance` | Aggregation on vw_ptl + canonical tables |
| GET | `/api/v1/dashboard/integration` | audit.refresh_status + audit.load_log |

#### Auth
| Method | Path |
|--------|------|
| POST | `/api/v1/auth/token` |

### 8.2 Backend Structure (Target)

```
backend/app/
  main.py
  config.py
  database.py
  auth/
    jwt_handler.py
    dependencies.py
  models/
    patient.py
    cancer_pathway.py
    radiology.py
    histology.py
    test_result.py
    cancer_treatment.py
    endoscopy.py
    mdt.py
    ipt.py
    tracking_comment.py
    inpatient_encounter.py
    outpatient_appointment.py
    reference.py
    audit.py
  schemas/
    patient_schema.py
    pathway_schema.py
    results_schema.py
    treatment_schema.py
    mdt_schema.py
    comment_schema.py
    reference_schema.py
    dashboard_schema.py
  repositories/
    patient_repository.py
    pathway_repository.py
    results_repository.py
    treatment_repository.py
    mdt_repository.py
    comment_repository.py
    encounter_repository.py
    ipt_repository.py
    reference_repository.py
    audit_repository.py
  services/
    patient_service.py
    pathway_service.py
    ptl_service.py
    results_service.py
    treatment_service.py
    mdt_service.py
    comment_service.py
    dashboard_service.py
    search_service.py
  api/v1/
    patients.py
    ptl.py
    mdt.py
    treatment.py
    comments.py
    results.py
    reference.py
    dashboard.py
    search.py
    auth.py
```

---

## 9. Frontend Plan

### 9.1 Screen Inventory (Target)

| Screen | Purpose | Key API Calls |
|--------|---------|---------------|
| PTL List | Main operational view — all open pathways, filterable by site/status/breach | `/api/v1/ptl`, `/api/v1/ptl/filters` |
| PTL Summary | Aggregated KPIs — breaches, volumes, site breakdown | `/api/v1/ptl/summary` |
| Patient 360 | Full patient detail with tabs | `/api/v1/patients/{id}` + sub-endpoints |
| Patient 360 → Summary | Demographics, pathway status, key dates | Patient + pathway data |
| Patient 360 → Pathway | Pathway timeline, breach dates, milestones | Pathway data |
| Patient 360 → Results | Radiology, histology, test results | Results endpoints |
| Patient 360 → MDT | MDT bookings, notes, outcomes | MDT endpoints |
| Patient 360 → Treatment | Treatment timeline, prescription status | Treatment endpoint |
| Patient 360 → Encounters | OP appointments + inpatient procedures | Encounters endpoint |
| Patient 360 → Endoscopy | Endoscopy exams and reports | Endoscopy endpoint |
| Patient 360 → Comments | Tracking comments | Comments endpoint |
| Patient 360 → IPT | Inter-provider transfers | IPT endpoint |
| MDT Schedule | Meeting list with booked patients | `/api/v1/mdt/meetings` |
| Search | Patient search by name, NHS number, MRN | `/api/v1/search` |
| Dashboard — Performance | Breach rates, wait times, site comparison | `/api/v1/dashboard/performance` |
| Dashboard — Integration | Data freshness, load status, errors | `/api/v1/dashboard/integration` |
| Actions | Action inbox | `/api/v1/actions` |

### 9.2 Frontend Structure (Target)

```
client/src/
  pages/
    PTL/
      PTLList.jsx
      PTLSummary.jsx
    Patient/
      Patient360.jsx
      tabs/
        SummaryTab.jsx
        PathwayTab.jsx
        ResultsTab.jsx
        MDTTab.jsx
        TreatmentTab.jsx
        EncountersTab.jsx
        EndoscopyTab.jsx
        CommentsTab.jsx
        IPTTab.jsx
    MDT/
      MDTSchedule.jsx
      MDTMeetingDetail.jsx
    Dashboard/
      PerformanceDashboard.jsx
      IntegrationDashboard.jsx
    Search/
      SearchPage.jsx
    Actions/
      ActionsInbox.jsx
  components/
    common/
      DataTable.jsx
      Timeline.jsx
      StatusBadge.jsx
      BreachIndicator.jsx
      RefreshTimestamp.jsx
      FilterBar.jsx
    patient/
      PatientHeader.jsx
      PathwayCard.jsx
      ResultCard.jsx
      TreatmentCard.jsx
      MDTNoteCard.jsx
      CommentCard.jsx
  hooks/
    usePatient.js
    usePTL.js
    useMDT.js
    useResults.js
    useTreatment.js
    useComments.js
    useReference.js
  api/
    client.js
    patients.js
    ptl.js
    mdt.js
    treatment.js
    comments.js
    reference.js
    dashboard.js
  context/
    AuthContext.js
    FilterContext.js
```

---

## 10. Phased Delivery Roadmap

### Phase 1 — Foundation (Weeks 1–2)

**Goal**: Database complete, reference data seeded, basic generator working.

| # | Task | Layer |
|---|------|-------|
| 1.1 | Create PostgreSQL schemas: raw, staging, canonical, ref, app, audit | Database |
| 1.2 | Create all canonical tables per spec (Section 4.4) | Database |
| 1.3 | Create raw tables (Section 4.2) | Database |
| 1.4 | Create staging tables (Section 4.3) | Database |
| 1.5 | Create audit tables (Section 4.7) | Database |
| 1.6 | Seed ref.cancer_site and ref.hospital_site | Database |
| 1.7 | Create generation_params.yaml with full parameter model | Generator |
| 1.8 | Create reference data seed files (ICD-10, test names, radiology types, etc.) | Generator |
| 1.9 | Build patient_generator.py | Generator |
| 1.10 | Build pathway_generator.py with timeline skeleton | Generator |

### Phase 2 — Generator Complete (Weeks 3–4)

**Goal**: All domains generate synthetic data in correct source formats.

| # | Task | Layer |
|---|------|-------|
| 2.1 | Build diagnosis_generator.py | Generator |
| 2.2 | Build radiology_generator.py | Generator |
| 2.3 | Build histology_generator.py | Generator |
| 2.4 | Build test_result_generator.py | Generator |
| 2.5 | Build treatment_generator.py | Generator |
| 2.6 | Build mdt_generator.py (meetings + bookings + notes) | Generator |
| 2.7 | Build appointment_generator.py | Generator |
| 2.8 | Build encounter_generator.py | Generator |
| 2.9 | Build endoscopy_generator.py | Generator |
| 2.10 | Build ipt_generator.py | Generator |
| 2.11 | Build comment_generator.py | Generator |
| 2.12 | Build hl7_renderer.py (pathology + radiology HL7 output) | Generator |
| 2.13 | Build csv_renderer.py (PAS, SACT, appointments, encounters, etc.) | Generator |
| 2.14 | Build xml_renderer.py (Somerset pathways) | Generator |
| 2.15 | Build json_renderer.py (MDT, e-RS) | Generator |
| 2.16 | Build orchestrator.py and run_generation.py CLI | Generator |
| 2.17 | Test: generate 50 patients end-to-end, validate output files | Generator |

### Phase 3 — Integration Engine Complete (Weeks 5–6)

**Goal**: All source formats flow through raw → staging → canonical.

| # | Task | Layer |
|---|------|-------|
| 3.1 | Build raw_loader.py (store original payloads) | Integration |
| 3.2 | Build hl7_parser.py | Integration |
| 3.3 | Build csv_parser.py | Integration |
| 3.4 | Build xml_parser.py | Integration |
| 3.5 | Build json_parser.py | Integration |
| 3.6 | Build staging_loader.py | Integration |
| 3.7 | Build patient_mapper.py + canonical_loader for patient | Integration |
| 3.8 | Build pathway_mapper.py + canonical_loader for cancer_pathway | Integration |
| 3.9 | Build radiology_mapper.py | Integration |
| 3.10 | Build histology_mapper.py | Integration |
| 3.11 | Build test_result_mapper.py | Integration |
| 3.12 | Build treatment_mapper.py | Integration |
| 3.13 | Build mdt_mapper.py (meeting + booking + note) | Integration |
| 3.14 | Build endoscopy_mapper.py | Integration |
| 3.15 | Build appointment_mapper.py + encounter_mapper.py | Integration |
| 3.16 | Build ipt_mapper.py | Integration |
| 3.17 | Build comment_mapper.py | Integration |
| 3.18 | Build reference_loader.py (seed ref tables) | Integration |
| 3.19 | Build audit_logger.py | Integration |
| 3.20 | Build error_handler.py | Integration |
| 3.21 | Build orchestrator.py (end-to-end pipeline controller) | Integration |
| 3.22 | Build replay.py (re-process from raw) | Integration |
| 3.23 | Test: generate 50 patients → run pipeline → verify all canonical tables populated | Integration |

### Phase 4 — API and Views (Weeks 7–8)

**Goal**: All data exposed through FastAPI.

| # | Task | Layer |
|---|------|-------|
| 4.1 | Create app.vw_ptl | Database |
| 4.2 | Create app.vw_patient_360 | Database |
| 4.3 | Create app.vw_mdt_schedule | Database |
| 4.4 | Create app.vw_results | Database |
| 4.5 | Create app.vw_treatment_timeline | Database |
| 4.6 | Create app.vw_tracking_comments | Database |
| 4.7 | Create app.vw_endoscopy | Database |
| 4.8 | Create app.vw_ipt | Database |
| 4.9 | Create app.vw_encounters | Database |
| 4.10 | Add/update SQLAlchemy models for all canonical tables | Backend |
| 4.11 | Add Pydantic schemas for all API responses | Backend |
| 4.12 | Build repository layer (Section 8.2) | Backend |
| 4.13 | Build service layer (PTL, pathway, results, MDT, treatment, comments) | Backend |
| 4.14 | Build/update API endpoints (Section 8.1) | Backend |
| 4.15 | Add reference endpoints | Backend |
| 4.16 | Add integration dashboard endpoint (audit tables) | Backend |
| 4.17 | Test: all endpoints return correct data for generated dataset | Backend |

### Phase 5 — Frontend Complete (Weeks 9–10)

**Goal**: All screens functional.

| # | Task | Layer |
|---|------|-------|
| 5.1 | Update PTL list to use new filters (cancer site, hospital site) | Frontend |
| 5.2 | Add PTL summary dashboard | Frontend |
| 5.3 | Build/complete Patient 360 Summary tab | Frontend |
| 5.4 | Build Patient 360 Pathway tab (timeline, breach indicators) | Frontend |
| 5.5 | Build Patient 360 Results tab (radiology + histology + test results) | Frontend |
| 5.6 | Build Patient 360 MDT tab (bookings, notes) | Frontend |
| 5.7 | Build Patient 360 Treatment tab (timeline, prescription status) | Frontend |
| 5.8 | Build Patient 360 Encounters tab (OP + inpatient) | Frontend |
| 5.9 | Build Patient 360 Endoscopy tab | Frontend |
| 5.10 | Build Patient 360 Comments tab | Frontend |
| 5.11 | Build Patient 360 IPT tab | Frontend |
| 5.12 | Build MDT Schedule screen | Frontend |
| 5.13 | Build Integration Dashboard screen (refresh status, load history, errors) | Frontend |
| 5.14 | Update Performance Dashboard | Frontend |
| 5.15 | Add RefreshTimestamp component (shows source freshness per table) | Frontend |
| 5.16 | Add search functionality | Frontend |

### Phase 6 — Mirth Integration (Weeks 11–12)

**Goal**: Mirth channels wired as an alternative integration path.

| # | Task | Layer |
|---|------|-------|
| 6.1 | Install Mirth Connect on Windows Server | Mirth |
| 6.2 | Create PAS Patient channel (CSV → canonical.patient) | Mirth |
| 6.3 | Create Somerset Pathway channel (XML → canonical.cancer_pathway) | Mirth |
| 6.4 | Create Pathology HL7 channel (HL7 → canonical.histology + test_result) | Mirth |
| 6.5 | Create Radiology HL7 channel (HL7 → canonical.radiology) | Mirth |
| 6.6 | Create SACT Treatment channel (CSV → canonical.cancer_treatment) | Mirth |
| 6.7 | Create MDT channel (JSON → canonical.mdt_*) | Mirth |
| 6.8 | Create remaining channels (endoscopy, appointments, encounters, IPT, comments) | Mirth |
| 6.9 | Create audit logging global channel | Mirth |
| 6.10 | Test: run same synthetic data through Mirth, verify identical canonical output | Mirth |

### Phase 7 — Hardening (Weeks 13–14)

**Goal**: Production-quality robustness.

| # | Task | Layer |
|---|------|-------|
| 7.1 | Add retry logic to integration engine | Integration |
| 7.2 | Add reconciliation checks (row counts, referential integrity) | Integration |
| 7.3 | Add role-based access to API | Backend |
| 7.4 | Add unit tests for generators | Testing |
| 7.5 | Add unit tests for mappers | Testing |
| 7.6 | Add integration tests (generate → pipeline → API → verify) | Testing |
| 7.7 | Add API endpoint tests | Testing |
| 7.8 | Write deployment documentation (Windows Server) | Docs |
| 7.9 | Write user guide (how to generate data, run pipeline, use app) | Docs |
| 7.10 | Performance test: generate 1000+ patients, measure pipeline and UI performance | Testing |

---

## 11. End-to-End Run Sequence (Target)

When complete, the full system runs like this:

```bash
# Step 1: Generate synthetic data
python source_systems/run_generation.py --config config/generation_params.yaml

# Step 2: Run integration pipeline
python integration_engine/orchestrator.py --source output/ --target postgresql://...

# Step 3: Start backend
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000

# Step 4: Start frontend
cd client && npm start

# Step 5: Open browser
# http://localhost:3000 → Cancer 360 UI with full synthetic data
```

Or with Mirth:

```bash
# Step 1: Generate synthetic data (same)
python source_systems/run_generation.py --config config/generation_params.yaml

# Step 2: Drop files into Mirth watched directories (or auto-routed)
# Mirth channels process automatically

# Step 3-5: Same as above
```

---

## 12. File Creation Checklist (First 30 Files)

| # | File | Layer |
|---|------|-------|
| 1 | `db/schemas/create_schemas.sql` | Database |
| 2 | `db/schemas/canonical/patient.sql` | Database |
| 3 | `db/schemas/canonical/cancer_pathway.sql` | Database |
| 4 | `db/schemas/canonical/ipt.sql` | Database |
| 5 | `db/schemas/canonical/tracking_comment.sql` | Database |
| 6 | `db/schemas/canonical/mdt_meeting.sql` | Database |
| 7 | `db/schemas/canonical/mdt_booking.sql` | Database |
| 8 | `db/schemas/canonical/mdt_note.sql` | Database |
| 9 | `db/schemas/canonical/inpatient_encounter.sql` | Database |
| 10 | `db/schemas/canonical/outpatient_appointment.sql` | Database |
| 11 | `db/schemas/canonical/cancer_treatment.sql` | Database |
| 12 | `db/schemas/canonical/endoscopy.sql` | Database |
| 13 | `db/schemas/canonical/radiology.sql` | Database |
| 14 | `db/schemas/canonical/histology.sql` | Database |
| 15 | `db/schemas/canonical/test_result.sql` | Database |
| 16 | `db/schemas/ref/cancer_site.sql` | Database |
| 17 | `db/schemas/ref/hospital_site.sql` | Database |
| 18 | `db/schemas/raw/raw_tables.sql` | Database |
| 19 | `db/schemas/audit/audit_tables.sql` | Database |
| 20 | `db/views/vw_ptl.sql` | Database |
| 21 | `db/views/vw_patient_360.sql` | Database |
| 22 | `db/views/vw_results.sql` | Database |
| 23 | `config/generation_params.yaml` | Generator |
| 24 | `source_systems/generators/patient_generator.py` | Generator |
| 25 | `source_systems/generators/pathway_generator.py` | Generator |
| 26 | `source_systems/generators/orchestrator.py` | Generator |
| 27 | `source_systems/renderers/hl7_renderer.py` | Generator |
| 28 | `source_systems/renderers/csv_renderer.py` | Generator |
| 29 | `integration_engine/orchestrator.py` | Integration |
| 30 | `integration_engine/loaders/canonical_loader.py` | Integration |

---

## 13. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Temporal inconsistency in generated data (dates out of order) | Unrealistic journeys, broken pathway logic | Pathway generator creates ordered timeline skeleton; all downstream generators respect it |
| HL7 parsing complexity | Incomplete or incorrect data extraction | Use well-tested HL7 library (python-hl7 or hl7apy); validate against known message samples |
| Schema drift between spec and implementation | UI shows wrong or missing data | Use the NNUH V5 spec as the single source of truth; automate schema validation |
| Mirth channel failures | Integration path broken | Keep Python pipeline as primary; Mirth is optional parallel path |
| Large volume performance (1000+ patients) | Slow generation, slow pipeline, slow UI | Batch inserts, database indexes on PKs and FKs, pagination on API endpoints |
| Windows Server compatibility | Path separators, service management, file watching | Test all scripts on Windows; use `pathlib` throughout; document Windows-specific setup |

---

## 14. Success Criteria

The system is complete when:

1. You can run `run_generation.py --config generation_params.yaml` with 500 patients and get valid source files in all formats.
2. You can run the integration pipeline and see all canonical tables populated with referentially consistent data.
3. Every field in the NNUH V5 spec is either stored in a canonical table or derivable in an app view.
4. The PTL shows all open pathways with correct breach flags, filterable by cancer site and hospital site.
5. Patient 360 shows every domain tab with real data for any generated patient.
6. MDT schedule shows meetings with booked patients and notes.
7. Integration dashboard shows refresh timestamps and load history.
8. The same synthetic data can be processed through either the Python pipeline or Mirth channels with identical results.
9. You can change generation parameters and regenerate a completely different dataset.
