# Cancer 360 Mirth Connect Blueprint

## Purpose

This document defines the concrete Mirth Connect design for **option 1**, where Mirth fully replaces the Python TIE layer in this repo.

Target architecture:

`source_systems -> Mirth Connect -> PostgreSQL CDM -> FastAPI`

Repo alignment:

- Source simulators stay in [source_systems](/c:/Users/MS234/Desktop/cancer360/source_systems)
- Target schema stays in [init.sql](/c:/Users/MS234/Desktop/cancer360/init.sql)
- API/UI stays in [backend](/c:/Users/MS234/Desktop/cancer360/backend)
- Python `tie` becomes optional reference logic only

## Scope

Mirth is responsible for:

- receiving HL7 over LLP/MLLP
- reading CSV drops from Windows folders
- validating source payloads
- transforming source data into the live Cancer 360 CDM
- writing to PostgreSQL
- audit logging
- dead-letter handling

Mirth is not responsible for:

- synthetic data generation
- frontend/API rendering
- clinical dashboard logic in the app

## Environment

Recommended Windows layout:

```text
C:\cancer360\
├── source_systems\
├── incoming\
│   ├── somerset\
│   ├── aria\
│   └── endoscopy\
├── mirth\
│   ├── exports\
│   ├── temp\
│   └── logs\
├── backend\
└── init.sql
```

Recommended Mirth runtime settings:

- Mirth version: `4.4+`
- JVM: `Java 17`
- LLP listener port: `2575`
- Database: PostgreSQL `cancer360`
- Timezone: local trust timezone, but store timestamps in UTC where possible

## Shared Mirth Configuration

### Code Templates

Create these global code templates in Mirth:

1. `UuidHelpers`
Functions:
- `deterministicUuid(namespace, value)`
- `newUuid()`

Implementation pattern:

```javascript
function deterministicUuid(namespace, value) {
    var bytes = new java.lang.String(namespace + ":" + value).getBytes("UTF-8");
    return java.util.UUID.nameUUIDFromBytes(bytes).toString();
}

function newUuid() {
    return java.util.UUID.randomUUID().toString();
}
```

2. `DateHelpers`
Functions:
- `parseIsoDate(value)`
- `parseHl7Timestamp(value)`
- `parseCsvBool(value)`

3. `CsvHelpers`
Functions:
- `splitCsvLine(line)`
- `parseCsv(rawText)`

4. `DbHelpers`
Functions:
- `queryScalar(conn, sql, params)`
- `executeUpdate(sql, params)`
- `resolvePatientId(nhsNumber)`
- `writeAudit(...)`
- `writeDlq(...)`

5. `SourceRouting`
Functions:
- `sendingApplication(msg)`
- `messageType(msg)`
- `filePrefix(fileName)`

### Database Connections

Create one PostgreSQL connection named `Cancer360Postgres`.

Use it from all channels.

### Folder Convention

Use Mirth file readers against:

- `C:\cancer360\incoming\somerset`
- `C:\cancer360\incoming\aria`
- `C:\cancer360\incoming\endoscopy`

Each file-reader channel should move processed files into:

- `processed\`
- `error\`

under the same source folder.

## Channel Inventory

### 1. `PAS_ADT`

Purpose:
- receive Cerner/PAS ADT events
- upsert `patient`
- optionally insert/update `episode` for inpatient events

Source connector:
- LLP Listener
- port `2575`
- receive HL7 v2.x

Filter:
- `MSH-3 = CERNER`
- `MSH-9 in ADT^A01, ADT^A03, ADT^A04`

Destination steps:

1. JavaScript transformer
- extract PID demographics
- normalize NHS number
- generate deterministic `patient_id`

2. Database Writer
- upsert `patient`

3. Conditional Database Writer
- for `ADT^A01` and `ADT^A03`, upsert `episode`

4. Audit Writer
- write `integration_audit_log`

Target tables:
- `patient`
- `episode`
- `integration_audit_log`

### 2. `PAS_SIU`

Purpose:
- receive outpatient scheduling events
- upsert `appointment`

Source connector:
- LLP Listener

Filter:
- `MSH-3 = CERNER`
- `MSH-9 in SIU^S12, SIU^S14`

Destination steps:

1. Resolve patient from NHS number
2. Upsert `appointment`
3. Write audit row

Target table:
- `appointment`

### 3. `ICE_ORU`

Purpose:
- receive pathology results
- write structured and narrative pathology data

Source connector:
- LLP Listener

Filter:
- `MSH-3 in WINPATH, ICE`
- `MSH-9 = ORU^R01`

Destination steps:

1. Parse PID / OBR / OBX
2. Resolve patient
3. Insert/upsert `pathology_result`
4. Insert/upsert `pathology_result_value` per numeric/coded OBX
5. If histopathology, derive structured fields into `histopath_structured`
6. Write audit row

Target tables:
- `pathology_result`
- `pathology_result_value`
- `histopath_structured`

### 4. `RIS_ORU`

Purpose:
- receive radiology reports
- write `radiology_result`

Source connector:
- LLP Listener

Filter:
- `MSH-3 in CRIS, RIS`
- `MSH-9 = ORU^R01`

Destination steps:

1. Parse PID / OBR / OBX
2. Resolve patient
3. Build report text and conclusion from OBX segments
4. Upsert `radiology_result`
5. Write audit row

Target tables:
- `radiology_result`

### 5. `ARIA_SIU`

Purpose:
- receive Aria appointment status updates
- reflect oncology bookings in `appointment`

Source connector:
- LLP Listener

Filter:
- `MSH-3 = ARIA`
- `MSH-9 in SIU^S12, SIU^S14`

Destination steps:

1. Parse SCH/PID
2. Resolve patient
3. Upsert `appointment`
4. Write audit row

Target table:
- `appointment`

### 6. `SOMERSET_PATHWAYS`

Purpose:
- process main Somerset PTL extract
- populate/refine referral, diagnosis, staging, pathway data

Source connector:
- File Reader
- pattern: `somerset_pathways_*.csv`

Destination steps:

1. Parse CSV rows
2. Upsert `patient` where needed
3. Upsert `referral`
4. Upsert `diagnosis`
5. Upsert `staging`
6. Upsert `cancer_pathway`
7. Write audit rows

Target tables:
- `patient`
- `referral`
- `diagnosis`
- `staging`
- `cancer_pathway`

### 7. `SOMERSET_TRACKING`

Purpose:
- process pathway tracking comments
- surface navigation work through `cancer_action`

Source connector:
- File Reader
- pattern: `somerset_tracking_*.csv`

Destination steps:

1. Resolve pathway from source `pathway_id`
2. Resolve patient via `cancer_pathway.patient_id`
3. Insert/upsert `cancer_action`

Recommended mapping:
- `comment_title -> action_type`
- `comment_text -> action_description`
- `created_by -> created_by`
- `created_at -> due_date` or `created_at` only
- `source_system = Somerset`

Target table:
- `cancer_action`

### 8. `SOMERSET_MDT`

Purpose:
- process MDT meetings, bookings, and outcome notes
- persist MDT decisions into `mdt_discussion`

Source connector:
- Either 3 file-reader channels or 1 dispatcher channel with filename routing

Patterns:
- `somerset_mdt_meetings_*.csv`
- `somerset_mdt_bookings_*.csv`
- `somerset_mdt_notes_*.csv`

Recommended design:

- `SOMERSET_MDT_MEETINGS_CACHE`
  - cache meeting metadata in channel/global map
- `SOMERSET_MDT_BOOKINGS_CACHE`
  - cache pathway-to-meeting mapping
- `SOMERSET_MDT_NOTES`
  - join cached context and upsert `mdt_discussion`

Target table:
- `mdt_discussion`

### 9. `SOMERSET_IPT`

Purpose:
- process inter-provider transfers
- represent them operationally in `cancer_action`

Source connector:
- File Reader
- pattern: `somerset_ipt_*.csv`

Recommended mapping:
- `tertiary_reason -> action_type`
- `tertiary_sending_comment -> action_description`
- `receiving_org_name -> notes`
- `tertiary_received_date -> due_date`
- `priority = high`
- `source_system = Somerset`

Target table:
- `cancer_action`

### 10. `ARIA_TREATMENT`

Purpose:
- process Aria treatment extracts
- split treatment rows into SACT or RT targets

Source connector:
- File Reader
- pattern: `aria_treatment_*.csv`

Routing inside transformer:

- `treatment_type in Chemotherapy, Immunotherapy`
  - upsert `sact_course`
  - upsert `sact_cycle`
  - upsert `sact_drug`

- `treatment_type = Radiotherapy`
  - upsert `radiotherapy_course`
  - upsert `radiotherapy_fraction`

Target tables:
- `sact_course`
- `sact_cycle`
- `sact_drug`
- `radiotherapy_course`
- `radiotherapy_fraction`

### 11. `ENDOSCOPY`

Purpose:
- process endoscopy CSV export
- expose endoscopy events operationally

Source connector:
- File Reader
- pattern: `endoscopy_*.csv`

Recommended mapping:

- upsert `appointment`
  - endoscopy attendance/reporting
- insert `cancer_action`
  - “Review endoscopy report”

Target tables:
- `appointment`
- `cancer_action`

## Shared Transformer Rules

### Patient Resolution

Always resolve patient in this order:

1. NHS number from source payload
2. `SELECT patient_id FROM patient WHERE nhs_number = ?`
3. If not found and sufficient demographics exist:
   - generate deterministic UUID
   - insert into `patient`

### Deterministic Keys

Use deterministic UUIDs for idempotency.

Recommended namespaces:

- `patient:{nhs_number}`
- `somerset-pathway:{source_pathway_id}`
- `somerset-referral:{source_pathway_id}`
- `somerset-diagnosis:{source_pathway_id}`
- `somerset-staging:{source_pathway_id}`
- `appointment:{source_appt_id}`
- `pathology:{accession}`
- `radiology:{accession}`
- `sact-course:{treatment_group_id}`
- `sact-cycle:{cancer_treatment_id}`
- `rt-course:{treatment_group_id}`
- `rt-fraction:{cancer_treatment_id}`

### Idempotency

Every channel should be re-runnable. Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`.

### Error Handling

On transformer or DB failure:

1. write raw payload and exception summary to `dead_letter_queue`
2. write failed event to `integration_audit_log`
3. set channel response to error/negative ACK for LLP sources
4. move file into `error\` for file-reader sources

## Audit and DLQ

### `integration_audit_log`

Write one audit record per processed message/file batch.

Minimum fields:

- `correlation_id`
- `event_type`
- `source_system`
- `message_type`
- `message_id`
- `entity_type`
- `entity_id`
- `status`
- `error_message`
- `raw_payload_hash`
- `processing_time_ms`

### `dead_letter_queue`

Write DLQ rows for:

- parse failures
- patient resolution failures when insert is not allowed
- DB constraint failures
- channel script exceptions

## Recommended Mirth Deploy Order

1. Create global code templates
2. Create DB connection
3. Create LLP channels:
   - `PAS_ADT`
   - `PAS_SIU`
   - `ICE_ORU`
   - `RIS_ORU`
   - `ARIA_SIU`
4. Create file-reader channels:
   - `SOMERSET_PATHWAYS`
   - `SOMERSET_TRACKING`
   - `SOMERSET_MDT_*`
   - `SOMERSET_IPT`
   - `ARIA_TREATMENT`
   - `ENDOSCOPY`
5. Deploy channels in disabled state
6. Verify DB writes with sample simulator output
7. Enable sources one by one

## Testing Sequence

Use the existing simulators in this repo:

1. Generate journeys

```powershell
.\.venv\Scripts\python.exe source_systems\scenario_engine.py --patients 20 --output data\scenarios\journeys.json
```

2. Generate payloads

```powershell
.\.venv\Scripts\python.exe source_systems\run_all.py --scenarios data\scenarios\journeys.json --output-dir data
```

3. Point live mode to Mirth instead of Python TIE

```powershell
.\.venv\Scripts\python.exe source_systems\run_all.py --scenarios data\scenarios\journeys.json --mode replay --mllp-host 127.0.0.1 --mllp-port 2575 --file-drop-dir C:\cancer360\incoming
```

4. Verify API

- `GET /api/v1/ptl`
- `GET /api/v1/patients/{nhs}`
- `GET /api/v1/patients/{nhs}/navigation`
- `GET /api/v1/integration/status`

## Channel-to-Table Matrix

| Channel | Tables |
|---|---|
| PAS_ADT | `patient`, `episode`, `integration_audit_log`, `dead_letter_queue` |
| PAS_SIU | `appointment`, `integration_audit_log`, `dead_letter_queue` |
| ICE_ORU | `pathology_result`, `pathology_result_value`, `histopath_structured`, `integration_audit_log`, `dead_letter_queue` |
| RIS_ORU | `radiology_result`, `integration_audit_log`, `dead_letter_queue` |
| ARIA_SIU | `appointment`, `integration_audit_log`, `dead_letter_queue` |
| SOMERSET_PATHWAYS | `patient`, `referral`, `diagnosis`, `staging`, `cancer_pathway`, `integration_audit_log`, `dead_letter_queue` |
| SOMERSET_TRACKING | `cancer_action`, `integration_audit_log`, `dead_letter_queue` |
| SOMERSET_MDT_* | `mdt_discussion`, `integration_audit_log`, `dead_letter_queue` |
| SOMERSET_IPT | `cancer_action`, `integration_audit_log`, `dead_letter_queue` |
| ARIA_TREATMENT | `sact_course`, `sact_cycle`, `sact_drug`, `radiotherapy_course`, `radiotherapy_fraction`, `integration_audit_log`, `dead_letter_queue` |
| ENDOSCOPY | `appointment`, `cancer_action`, `integration_audit_log`, `dead_letter_queue` |

## Practical Recommendation

If you build this in Mirth, use the Python `tie` code as reference only for:

- route expectations
- idempotent key design
- field mapping intent
- sample payload assumptions

Do not try to run both Mirth and Python TIE as active writers to the same database at the same time.
