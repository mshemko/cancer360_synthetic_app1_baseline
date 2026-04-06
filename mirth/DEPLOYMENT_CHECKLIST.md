# Mirth Deployment Checklist

Use this checklist when building the Cancer 360 Mirth implementation in Mirth Administrator on Windows.

## 1. Prepare The Host

- Install Mirth Connect `4.4+` on the Windows Server.
- Install Java `17` if the chosen Mirth build requires it.
- Confirm PostgreSQL connectivity from the Mirth host to the Cancer 360 database.
- Create these folders:
  - `C:\cancer360\incoming\somerset`
  - `C:\cancer360\incoming\somerset\processed`
  - `C:\cancer360\incoming\somerset\error`
  - `C:\cancer360\incoming\aria`
  - `C:\cancer360\incoming\aria\processed`
  - `C:\cancer360\incoming\aria\error`
  - `C:\cancer360\incoming\endoscopy`
  - `C:\cancer360\incoming\endoscopy\processed`
  - `C:\cancer360\incoming\endoscopy\error`
- Open inbound TCP `2575` for HL7 MLLP if source systems are external to the host.

## 2. Create Shared Mirth Assets

- Create one PostgreSQL database connection named `Cancer360Postgres`.
- Load the global code templates from [mirth/code_templates](c:/Users/MS234/Desktop/cancer360/mirth/code_templates):
  - `uuid_helpers.js`
  - `date_helpers.js`
  - `csv_helpers.js`
  - `db_helpers.js`
  - `source_helpers.js`
- Create channel or global properties for:
  - `db.url`
  - `db.username`
  - `db.password`
- Load the SQL statements from [mirth/sql/upserts.sql](c:/Users/MS234/Desktop/cancer360/mirth/sql/upserts.sql) and assign them to the keys documented in [mirth/sql/README.md](c:/Users/MS234/Desktop/cancer360/mirth/sql/README.md).

## 3. Build Channels In Order

- Build the HL7 channels first:
  1. `PAS_ADT`
  2. `PAS_SIU`
  3. `ICE_ORU`
  4. `RIS_ORU`
  5. `ARIA_SIU`
- Build the file-reader channels next:
  6. `SOMERSET_PATHWAYS`
  7. `SOMERSET_TRACKING`
  8. `SOMERSET_MDT`
  9. `SOMERSET_IPT`
  10. `ARIA_TREATMENT`
  11. `ENDOSCOPY`
- Use the XML scaffolds in [mirth/channel_xml](c:/Users/MS234/Desktop/cancer360/mirth/channel_xml) as the build reference for source connector settings, destination order, and dependencies.
- For each channel, paste the matching transformer from [mirth/channels/transformers](c:/Users/MS234/Desktop/cancer360/mirth/channels/transformers).

## 4. Channel-Specific Setup Notes

- Put all HL7 channels on port `2575` and route by `MSH-3` plus `MSH-9`.
- Set file readers to move successful files into the `processed` folder and failures into the `error` folder.
- For `SOMERSET_MDT`, ensure `somerset_mdt_meetings_*.csv` is processed before bookings or notes, because the transformer uses `globalMap` to cache meeting metadata.
- For `ARIA_TREATMENT`, confirm all SACT and radiotherapy SQL keys are loaded before deployment.
- For `ENDOSCOPY`, confirm the database already contains patient and pathway context from PAS and Somerset before replaying endoscopy extracts.

## 5. First Deployment Validation

- Deploy all code templates first.
- Deploy one channel at a time and validate that it starts cleanly.
- Send or drop one known-good sample per channel type.
- Confirm expected writes in:
  - `patient`
  - `appointment`
  - `episode`
  - `pathology_result`
  - `radiology_result`
  - `cancer_pathway`
  - `cancer_action`
  - `mdt_discussion`
  - `sact_course`
  - `radiotherapy_course`
- Confirm audit logging in `integration_audit_log`.
- Confirm failures land in `dead_letter_queue`.

## 6. Recommended Smoke Test Sequence

1. Replay PAS HL7 first so patient identity exists.
2. Replay Somerset pathways so referral and pathway context exists.
3. Replay Somerset tracking, MDT, and IPT files.
4. Replay ICE and RIS HL7.
5. Replay Aria SIU and Aria treatment CSV.
6. Replay Endoscopy last.
7. Verify the backend endpoints still populate from PostgreSQL:
   - `/api/v1/integration/status`
   - `/api/v1/patients/{nhs_number}`
   - `/api/v1/patients/{nhs_number}/navigation`

## 7. Handover Notes

- Keep the Python `source_systems` package as the replay and synthetic data driver.
- Treat the Python `tie` package as reference logic only once Mirth is in use.
- If you later want true importable Mirth exports, build the channels in Administrator using these scaffolds and export the resulting channels from the live Mirth instance.
